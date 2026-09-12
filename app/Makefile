# Build the API-7 APK inside the pinned 2014 ADT container.
# Usage: make debug | make clean | make shell | make install
IMAGE  := nook-adt:latest
# The debug keystore must persist across runs: Ant generates it on the fly, and
# a fresh key every build makes every reinstall fail with
# INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES.
#
# It has to be mounted at /home/ubuntu specifically. Ant's DebugKeyProvider asks
# the JVM for `user.home`, which on Linux comes from /etc/passwd — uid 1000 is
# `ubuntu` in this image — and ignores $HOME. ANT_OPTS pins it too, belt and
# braces.
HOMEDIR := $(CURDIR)/.androidhome
DOCKER := docker run --rm -u $(shell id -u):$(shell id -g) \
          -e HOME=/home/ubuntu -e ANT_OPTS=-Duser.home=/home/ubuntu \
          -v $(HOMEDIR):/home/ubuntu \
          -v $(CURDIR):/work/app -w /work/app $(IMAGE)

.PHONY: image debug clean shell install

image:
	docker build -t $(IMAGE) tools

debug: | $(HOMEDIR)
	# Resource IDs are inlined into Java classes. This old Ant build does not
	# reliably recompile their callers when aapt renumbers IDs after XML edits.
	$(DOCKER) ant clean debug

# keytool will not create the directory itself.
$(HOMEDIR):
	mkdir -p $(HOMEDIR)/.android

clean:
	$(DOCKER) ant clean

shell: | $(HOMEDIR)
	docker run --rm -it -u $(shell id -u):$(shell id -g) \
	  -e HOME=/home/ubuntu -e ANT_OPTS=-Duser.home=/home/ubuntu \
	  -v $(HOMEDIR):/home/ubuntu \
	  -v $(CURDIR):/work/app -w /work/app $(IMAGE) bash

# Runs on the host, where the Nook is actually plugged in.
install:
	adb install -r bin/NookPanel-debug.apk
