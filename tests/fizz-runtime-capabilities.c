/* Read-only static ChromeOS runtime capabilities probe. */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/utsname.h>

static void print_selected(const char *path, const char *prefix) {
    FILE *f=fopen(path,"r");
    if (!f) { printf("%s_UNAVAILABLE\n",prefix); return; }
    char line[1024];
    while (fgets(line,sizeof line,f)) {
        if (!strncmp(line,"Uid:",4) || !strncmp(line,"Gid:",4) ||
            !strncmp(line,"NoNewPrivs:",11) || !strncmp(line,"Seccomp:",8) ||
            !strncmp(line,"CapEff:",7)) {
            line[strcspn(line,"\r\n")]='\0';
            printf("%s_%s\n",prefix,line);
        }
    }
    fclose(f);
}
static void print_context(void) {
    FILE *f=fopen("/proc/self/attr/current","r");
    if (!f) { puts("SELINUX_CONTEXT_UNAVAILABLE"); return; }
    char line[512];
    if (fgets(line,sizeof line,f)) {
        line[strcspn(line,"\r\n")]='\0';
        printf("SELINUX_CONTEXT=%s\n",line);
    }
    fclose(f);
}
int main(void) {
    struct utsname u;
    if (uname(&u)) { perror("uname"); return 1; }
    printf("RUNTIME_ARCH=%s\n",u.machine);
    printf("RUNTIME_KERNEL=%s\n",u.release);
    printf("RUNTIME_UID=%lu\n",(unsigned long)getuid());
    printf("RUNTIME_EUID=%lu\n",(unsigned long)geteuid());
    printf("RUNTIME_GID=%lu\n",(unsigned long)getgid());
    print_selected("/proc/self/status","STATUS");
    print_context();
    puts("FIZZ_RUNTIME_CAPABILITIES_COMPLETE");
    return 0;
}
