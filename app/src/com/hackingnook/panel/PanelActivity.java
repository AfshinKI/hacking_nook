package com.hackingnook.panel;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.Handler;
import android.text.format.DateFormat;
import android.view.View;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.Date;

/**
 * Fullscreen image panel. Wakes, fetches an image from the configured URL,
 * draws it, then waits for the next interval.
 *
 * v0.1 keeps the screen on the whole time (~60 h of battery). Deep sleep —
 * writing the image as the Nook screensaver and setting an RTC alarm, which is
 * what gets you 30+ days — comes next; see docs/06-our-own-app.md.
 */
public class PanelActivity extends Activity {

    private ImageView image;
    private TextView status;
    private BatteryView battery;
    private final BroadcastReceiver batteryReceiver = new BroadcastReceiver() {
        public void onReceive(Context context, Intent intent) {
            int level = intent.getIntExtra("level", -1);
            int scale = intent.getIntExtra("scale", -1);
            int state = intent.getIntExtra("status", BatteryManager.BATTERY_STATUS_UNKNOWN);
            int percent = level >= 0 && scale > 0
                    ? (int) Math.min(100L, level * 100L / scale) : -1;
            battery.setBattery(percent, state == BatteryManager.BATTERY_STATUS_CHARGING);
        }
    };

    private final Handler handler = new Handler();
    private Runnable tick;
    private boolean fetching;
    private long lastFetchAt;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.panel);

        image = (ImageView) findViewById(R.id.panel_image);
        status = (TextView) findViewById(R.id.panel_status);
        battery = (BatteryView) findViewById(R.id.panel_battery);

        // BootReceiver starts us behind the Nook's keyguard. Bring the panel
        // onto the screen and dismiss the slide lock without a button press.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                | WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                | WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD
                | WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON);

        View.OnLongClickListener menuListener = new View.OnLongClickListener() {
            public boolean onLongClick(View v) {
                showMenu();
                return true;
            }
        };
        image.setOnLongClickListener(menuListener);
        status.setOnLongClickListener(menuListener);
        battery.setOnLongClickListener(menuListener);

        tick = new Runnable() {
            public void run() {
                refresh();
                handler.postDelayed(this, Config.intervalSeconds(PanelActivity.this) * 1000L);
            }
        };
    }

    @Override
    protected void onResume() {
        super.onResume();
        registerReceiver(batteryReceiver, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        handler.removeCallbacks(tick);

        // Anything that steals focus — the Nook's own "USB Mode" dialog is the
        // usual culprit — pauses and resumes us. Refetching on every resume
        // hammers the server and burns an e-ink refresh each time, so only go
        // out to the network if the image we are showing is actually stale.
        long age = System.currentTimeMillis() - lastFetchAt;
        long interval = Config.intervalSeconds(this) * 1000L;
        if (lastFetchAt == 0L || age >= interval) {
            handler.post(tick);
        } else {
            handler.postDelayed(tick, interval - age);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        unregisterReceiver(batteryReceiver);
        handler.removeCallbacks(tick);
    }

    private void refresh() {
        final String url = Config.url(this);
        if (url.length() == 0) {
            showStatus(getString(R.string.waiting));
            return;
        }
        if (fetching) {
            return;
        }
        fetching = true;

        new Thread(new Runnable() {
            public void run() {
                final Bitmap bitmap = ImageFetcher.fetch(url);
                handler.post(new Runnable() {
                    public void run() {
                        fetching = false;
                        lastFetchAt = System.currentTimeMillis();
                        if (bitmap == null) {
                            // A failed refresh must not replace the last good frame.
                            // Keep retrying on the normal schedule; only show an
                            // error when we have never displayed an image.
                            if (image.getDrawable() != null) {
                                status.setVisibility(View.GONE);
                                image.setVisibility(View.VISIBLE);
                                battery.setVisibility(View.VISIBLE);
                            } else {
                                showStatus("Could not fetch\n" + url + "\n\nLast try: " + now()
                                        + "\n\nLong press for settings.");
                            }
                        } else {
                            show(bitmap);
                        }
                    }
                });
            }
        }).start();
    }

    private void show(Bitmap bitmap) {
        battery.setVisibility(View.VISIBLE);
        status.setVisibility(View.GONE);
        image.setVisibility(View.VISIBLE);

        Bitmap previous = null;
        if (image.getDrawable() instanceof android.graphics.drawable.BitmapDrawable) {
            previous = ((android.graphics.drawable.BitmapDrawable) image.getDrawable()).getBitmap();
        }
        image.setImageBitmap(bitmap);
        // 256 MB of RAM and no generational GC worth the name: free it ourselves.
        if (previous != null && previous != bitmap) {
            previous.recycle();
        }
    }

    private void showStatus(String text) {
        battery.setVisibility(View.GONE);
        image.setVisibility(View.GONE);
        status.setVisibility(View.VISIBLE);
        status.setText(text);
    }

    private String now() {
        return DateFormat.getTimeFormat(this).format(new Date());
    }

    private void showMenu() {
        final CharSequence[] items = new CharSequence[] {
                getString(R.string.refresh_now),
                getString(R.string.settings),
        };
        new AlertDialog.Builder(this)
                .setTitle(R.string.menu_title)
                .setItems(items, new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int which) {
                        if (which == 0) {
                            refresh();
                        } else {
                            startActivity(new Intent(PanelActivity.this, SettingsActivity.class));
                        }
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }
}
