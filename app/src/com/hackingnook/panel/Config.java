package com.hackingnook.panel;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Everything NookPanel remembers. Kept in one place so the settings screen and
 * the display activity cannot disagree about key names.
 */
public final class Config {

    public static final String PREFS = "nookpanel";
    public static final String KEY_URL = "url";
    public static final String KEY_INTERVAL = "interval_seconds";

    /** Long enough that a full e-ink refresh is not constantly flashing. */
    public static final int DEFAULT_INTERVAL_SECONDS = 3600;

    private Config() {
    }

    public static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String url(Context context) {
        return prefs(context).getString(KEY_URL, "");
    }

    public static int intervalSeconds(Context context) {
        int value = prefs(context).getInt(KEY_INTERVAL, DEFAULT_INTERVAL_SECONDS);
        // A pathological interval would pin the CPU and murder the battery.
        return value < 10 ? 10 : value;
    }

    public static void save(Context context, String url, int intervalSeconds) {
        SharedPreferences.Editor editor = prefs(context).edit();
        editor.putString(KEY_URL, url == null ? "" : url.trim());
        editor.putInt(KEY_INTERVAL, intervalSeconds);
        editor.commit();
    }
}
