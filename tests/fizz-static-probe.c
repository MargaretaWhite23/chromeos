/* Read-only diagnostic executable, no ChromeOS installation or modification. */
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>

static void show_release(const char *path) {
    FILE *f = fopen(path, "r");
    if (f == NULL) {
        printf("RELEASE_FILE_UNAVAILABLE=%s\n", path);
        return;
    }
    printf("RELEASE_FILE=%s\n", path);
    char line[512];
    int count = 0;
    while (count < 24 && fgets(line, sizeof(line), f) != NULL) {
        if (strchr(line, '\n') == NULL) {
            int c;
            while ((c = fgetc(f)) != '\n' && c != EOF) {}
        }
        line[strcspn(line, "\r\n")] = '\0';
        printf("RELEASE_LINE=%s\n", line);
        ++count;
    }
    fclose(f);
}
int main(void) {
    struct utsname u;
    if (uname(&u) != 0) {
        perror("uname");
        return 1;
    }
    printf("KERNEL_SYSNAME=%s\n", u.sysname);
    printf("KERNEL_RELEASE=%s\n", u.release);
    printf("ARCHITECTURE=%s\n", u.machine);
    show_release("/etc/lsb-release");
    show_release("/etc/os-release");
    puts("FIZZ_STATIC_PROBE_COMPLETE");
    return 0;
}
