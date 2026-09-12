package com.hackingnook.panel;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.net.wifi.WifiManager;
import android.os.PowerManager;
import android.provider.Settings;
import android.util.Log;

/** API-7 wake alarms and the Nook's natural screen-off path. */
final class PowerCycle {
    static final String AUTOMATIC = "automatic_refresh";
    static boolean alarmStarting;
    static boolean settingsOpen;
    private static PowerManager.WakeLock cycleLock;
    private static final String TIMEOUT = "saved_screen_timeout";
    private static final String RESTORE = "restore_screen_timeout";

    static void schedule(Context context, long when) {
        Intent intent = new Intent(context, RefreshReceiver.class);
        PendingIntent pending = PendingIntent.getBroadcast(context, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT);
        ((AlarmManager) context.getSystemService(Context.ALARM_SERVICE)).set(
                AlarmManager.RTC_WAKEUP, when, pending);
        Config.prefs(context).edit().putLong("next_refresh_at", when).commit();
        Log.i("NookPanel", "next wake at " + when);
    }

    static void acquire(Context context) {
        if (cycleLock == null) {
            PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
            cycleLock = pm.newWakeLock(PowerManager.SCREEN_DIM_WAKE_LOCK
                    | PowerManager.ACQUIRE_CAUSES_WAKEUP, "NookPanel:refresh");
            cycleLock.setReferenceCounted(false);
        }
        cycleLock.acquire(90000L);
    }

    static void release() {
        if (cycleLock != null && cycleLock.isHeld()) cycleLock.release();
    }

    static void wifi(Context context, boolean enabled) {
        WifiManager wifi = (WifiManager) context.getSystemService(Context.WIFI_SERVICE);
        if (wifi != null && wifi.isWifiEnabled() != enabled) wifi.setWifiEnabled(enabled);
    }

    static void forceSleep(Context context) {
        int current = Settings.System.getInt(context.getContentResolver(),
                Settings.System.SCREEN_OFF_TIMEOUT, 120000);
        if (current > 1000) {
            Config.prefs(context).edit().putInt(TIMEOUT, current).commit();
        }
        // Persist the recovery flag before shortening the system-wide timeout.
        Config.prefs(context).edit().putBoolean(RESTORE, true).commit();
        Settings.System.putInt(context.getContentResolver(), Settings.System.SCREEN_OFF_TIMEOUT, 1000);
    }

    static void restoreTimeout(Context context) {
        if (!Config.prefs(context).getBoolean(RESTORE, false)) return;
        int saved = Config.prefs(context).getInt(TIMEOUT, 120000);
        if (saved <= 1000) saved = 120000;
        if (Settings.System.putInt(context.getContentResolver(), Settings.System.SCREEN_OFF_TIMEOUT, saved)) {
            Config.prefs(context).edit().putBoolean(RESTORE, false).commit();
        }
    }
}
