# Build Tesseract for ChromeOS Fizz

The [Tesseract OCR for ChromeOS x86_64 workflow](../.github/workflows/tesseract-chromeos.yml) builds Tesseract 5.5.1 from source entirely in GitHub Actions. It runs on `ubuntu-24.04` inside an Alpine 3.21 x86-64 container. The output is a portable musl package for Fizz. It carries its own runtime and needs no compiler or Alpine installation on the Chromebook.

## Run the build

Open [the workflow in GitHub Actions](https://github.com/MargaretaWhite23/chromeos/actions/workflows/tesseract-chromeos.yml), select **Run workflow**, and choose `main` for a versioned release. A push that changes the workflow file also triggers a build.

1. Alpine supplies GCC, CMake, Ninja, Leptonica development headers, and the English trained data. CMake builds the upstream `5.5.1` tag in Release mode with training tools, tests, and OpenMP disabled.
2. The packaging step reads ELF `DT_NEEDED` entries with `readelf -d` and recursively copies dependencies under their requested names. The ZIP contains the launcher, `bin/tesseract.real`, the musl loader and shared libraries in `lib/`, and `tessdata/eng.traineddata`. The launcher sets `TESSDATA_PREFIX` and starts the bundled loader with `--library-path` pointed at the package's `lib/`.
3. CI checks the ZIP's SHA-256, extracts it, runs the launcher with a clean environment, and checks that `eng` is listed in a BusyBox chroot containing only the extracted package.
4. A successful run uploads the ZIP and its checksum as the `tesseract-chromeos-x86_64-musl` Actions artifact. Builds on `main` also publish both files under the release tag `tesseract-chromeos-<run-number>`.

## Download and verify on Fizz

Download the two files from the same run or release. For an Actions artifact, the following example uses the authenticated GitHub CLI in Crostini and assumes ChromeOS Downloads is shared with Linux.

```sh
stage=/mnt/chromeos/MyFiles/Downloads/tesseract-fizz-42489484560
mkdir -p "$stage"
gh run download 42489484560 -R MargaretaWhite23/chromeos \
  -n tesseract-chromeos-x86_64-musl -D "$stage"
```

On the ChromeOS host, verify and smoke-test the archive from an executable directory under `/usr/local`. Run as an account with write access to `/usr/local/opt`.

```sh
(
  set -eu
  cd /home/chronos/user/MyFiles/Downloads/tesseract-fizz-42489484560
  sha256sum -c tesseract-chromeos-x86_64-musl.zip.sha256
  stage="$(mktemp -d /usr/local/opt/.tesseract-test.XXXXXX)"
  trap 'rm -rf "$stage"' EXIT
  unzip -q tesseract-chromeos-x86_64-musl.zip -d "$stage"
  env -i PATH=/usr/bin:/bin "$stage/tesseract" --version
  env -i PATH=/usr/bin:/bin "$stage/tesseract" --list-langs
)
```

For the existing Fizz installation, keep a backup of `/usr/local/opt/tesseract` before replacing it with the complete extracted directory. Repeat both checks through `/usr/local/bin/tesseract` after switching. Restore the backup if either check fails.

[Run 42489484560](https://github.com/MargaretaWhite23/chromeos/actions/runs/42489484560) passed CI and was installed on Fizz running ChromeOS `16700.66.0` with kernel `5.4.302`. The installed launcher reported Tesseract 5.5.1, Leptonica 1.84.1, and English (`eng`). This verified startup and language discovery. OCR on an image was outside that smoke test.

## Diagnose missing libraries

The earlier Fizz install contained the musl loader alone in its `lib/` directory. If the loader reports missing `libleptonica.so.6`, `libstdc++.so.6`, or `libgcc_s.so.1`, check that the entire verified ZIP was extracted and that the launcher is resolving `lib/` relative to the installed package. The isolated CI check catches missing dependencies before publication.
