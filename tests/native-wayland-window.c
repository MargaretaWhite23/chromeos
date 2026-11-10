#define _POSIX_C_SOURCE 200809L
#include <wayland-client.h>
#include "xdg-shell-client-protocol.h"
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#define WIDTH 640
#define HEIGHT 480
static struct wl_compositor *compositor;
static struct wl_shm *shm;
static struct xdg_wm_base *wm;
static struct wl_surface *surface;
static struct xdg_surface *xs;
static struct xdg_toplevel *top;
static struct wl_buffer *buffer;
static int configured=0;
static volatile sig_atomic_t running=1;
static void stop(int sig){(void)sig;running=0;}
static void registry_global(void *data,struct wl_registry *r,uint32_t name,const char *iface,uint32_t ver){
 (void)data;
 if(!strcmp(iface,"wl_compositor")) compositor=wl_registry_bind(r,name,&wl_compositor_interface,ver<3?ver:3);
 else if(!strcmp(iface,"wl_shm")) shm=wl_registry_bind(r,name,&wl_shm_interface,1);
 else if(!strcmp(iface,"xdg_wm_base")) wm=wl_registry_bind(r,name,&xdg_wm_base_interface,ver<3?ver:3);
}
static void registry_remove(void *d,struct wl_registry *r,uint32_t name){(void)d;(void)r;(void)name;}
static const struct wl_registry_listener reg_listener={registry_global,registry_remove};
static void wm_ping(void *d,struct xdg_wm_base *w,uint32_t serial){(void)d;xdg_wm_base_pong(w,serial);}
static const struct xdg_wm_base_listener wm_listener={wm_ping};
static void xs_configure(void *d,struct xdg_surface *x,uint32_t serial){
 (void)d;xdg_surface_ack_configure(x,serial);
 wl_surface_attach(surface,buffer,0,0);
 wl_surface_damage(surface,0,0,WIDTH,HEIGHT);
 wl_surface_commit(surface);
 configured=1;
 puts("WAYLAND_XDG_CONFIGURED");fflush(stdout);
}
static const struct xdg_surface_listener xs_listener={xs_configure};
static void top_configure(void *d,struct xdg_toplevel *t,int32_t w,int32_t h,struct wl_array *states){(void)d;(void)t;(void)w;(void)h;(void)states;}
static void top_close(void *d,struct xdg_toplevel *t){(void)d;(void)t;running=0;}
static void top_bounds(void *d,struct xdg_toplevel *t,int32_t w,int32_t h){(void)d;(void)t;printf("WAYLAND_TOPLEVEL_BOUNDS %d %d\\n",w,h);fflush(stdout);}
static void top_capabilities(void *d,struct xdg_toplevel *t,struct wl_array *caps){(void)d;(void)t;(void)caps;}
static const struct xdg_toplevel_listener top_listener={
 .configure=top_configure,
 .close=top_close,
 .configure_bounds=top_bounds,
 .wm_capabilities=top_capabilities
};
int main(void){
 signal(SIGTERM,stop);signal(SIGINT,stop);
 struct wl_display *display=wl_display_connect(NULL);
 if(!display){perror("wl_display_connect");return 2;}
 struct wl_registry *registry=wl_display_get_registry(display);
 wl_registry_add_listener(registry,&reg_listener,NULL);
 if(wl_display_roundtrip(display)<0){puts("WAYLAND_REGISTRY_FAILED");return 3;}
 if(!compositor||!shm||!wm){puts("WAYLAND_REQUIRED_GLOBAL_MISSING");return 4;}
 xdg_wm_base_add_listener(wm,&wm_listener,NULL);
 int fd=-1;
 char name[]="/tmp/native-wayland-XXXXXX";
 fd=mkstemp(name);
 if(fd<0){perror("mkstemp");return 5;}
 unlink(name);
 size_t bytes=WIDTH*HEIGHT*4;
 if(ftruncate(fd,(off_t)bytes)){perror("ftruncate");return 6;}
 uint32_t *pixels=mmap(NULL,bytes,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
 if(pixels==MAP_FAILED){perror("mmap");return 7;}
 for(int y=0;y<HEIGHT;y++)for(int x=0;x<WIDTH;x++)
  pixels[y*WIDTH+x]=(x/32+y/32)%2?0xff167ac6:0xff25a876;
 struct wl_shm_pool *pool=wl_shm_create_pool(shm,fd,(int)bytes);
 buffer=wl_shm_pool_create_buffer(pool,0,WIDTH,HEIGHT,WIDTH*4,WL_SHM_FORMAT_XRGB8888);
 wl_shm_pool_destroy(pool);
 close(fd);
 surface=wl_compositor_create_surface(compositor);
 xs=xdg_wm_base_get_xdg_surface(wm,surface);
 xdg_surface_add_listener(xs,&xs_listener,NULL);
 top=xdg_surface_get_toplevel(xs);
 xdg_toplevel_add_listener(top,&top_listener,NULL);
 xdg_toplevel_set_title(top,"Native ChromeOS Wayland Test");
 xdg_toplevel_set_app_id(top,"native-wayland-test");
 wl_surface_commit(surface);
 puts("WAYLAND_WINDOW_REQUESTED");fflush(stdout);
 /* Keep the event loop alive until closed or externally terminated. */
 int dispatch_result=0;
 while(running && (dispatch_result=wl_display_dispatch(display))>=0){}
 if(dispatch_result<0){
  int err=wl_display_get_error(display);
  const struct wl_interface *iface=NULL;
  uint32_t object_id=0;
  uint32_t protocol=wl_display_get_protocol_error(display,&iface,&object_id);
  fprintf(stderr,"WAYLAND_DISPATCH_ERROR errno=%d protocol=%u interface=%s object=%u\\n",err,protocol,iface?iface->name:"none",object_id);
 }
 printf("WAYLAND_WINDOW_EXIT configured=%d\n",configured);
 return configured?0:8;
}
