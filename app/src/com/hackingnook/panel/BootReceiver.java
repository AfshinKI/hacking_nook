package com.hackingnook.panel;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Starts the panel when the Nook finishes booting.
 *
 * Without this the app is effectively unreachable: the stock B&N home
 * (com.bn.nook.home) has no general app drawer, so a sideloaded APK never
 * appears anywhere on screen. A wall-mounted dashboard should come back by
 * itself after a power cut anyway.
 */
public class BootReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            return;
        }
        if (Config.url(context).length() == 0) {
            // Nothing configured yet — do not shove an empty panel in the way.
            Log.i("NookPanel", "boot: no URL configured, not starting");
            return;
        }
        Intent panel = new Intent(context, PanelActivity.class);
        panel.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(panel);
    }
}
