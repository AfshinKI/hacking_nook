package com.hackingnook.panel;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/** Manifest receiver: alarms still work if Android has killed the panel process. */
public class RefreshReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Config.url(context).length() == 0) return;
        // Arm a fallback before launching, even if launch or the fetch fails.
        PowerCycle.schedule(context, System.currentTimeMillis()
                + Config.intervalSeconds(context) * 1000L);
        if (PowerCycle.settingsOpen) return;
        PowerCycle.alarmStarting = true;
        PowerCycle.acquire(context);
        try {
            Intent panel = new Intent(context, PanelActivity.class);
            panel.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            panel.putExtra(PowerCycle.AUTOMATIC, true);
            context.startActivity(panel);
        } catch (RuntimeException e) {
            PowerCycle.alarmStarting = false;
            PowerCycle.release();
            Log.e("NookPanel", "alarm launch failed", e);
        }
    }
}
