# Build environment for Android 2.1 / API 7 APKs.
#
# Modern Android Studio + AGP cannot target API 7 at all. The only practical
# route is the last ADT bundle Google shipped (July 2014), which still contains
# the Ant-based build system plus aapt/dx. On x86_64 hosts those binaries run
# natively (they are 32-bit, hence lib32*); JDK 8 is the newest JDK the 2014
# Ant scripts tolerate.
#
# The bundle ships only the android-20 platform, so that is the *compile*
# target. Runtime target stays API 7 via AndroidManifest.xml uses-sdk.
FROM eclipse-temurin:8-jdk

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip ant lib32stdc++6 lib32z1 make \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/adt && \
    curl -fL "http://dl.google.com/android/adt/adt-bundle-linux-x86_64-20140702.zip" \
         -o /tmp/adt.zip && \
    unzip -q /tmp/adt.zip -d /opt/adt && \
    rm /tmp/adt.zip && \
    chmod -R a+rX /opt/adt && \
    find /opt/adt -type f \( -name "*.sh" -o -name "ant" -o -name "adb" \
         -o -name "aapt" -o -name "dx" -o -name "aidl" -o -name "android" \
         -o -name "zipalign" \) -exec chmod a+x {} +

ENV ANDROID_HOME=/opt/adt/adt-bundle-linux-x86_64-20140702/sdk
ENV PATH="${ANDROID_HOME}/tools:${ANDROID_HOME}/platform-tools:${ANDROID_HOME}/build-tools/android-4.4W:${PATH}"

WORKDIR /work
