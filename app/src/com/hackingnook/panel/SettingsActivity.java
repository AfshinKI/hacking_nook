package com.hackingnook.panel;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

/**
 * Two fields and a button. Deliberately not PreferenceActivity — typing a URL
 * on an infrared touchscreen is painful enough without nested preference
 * screens, and the same values can be pushed over adb (see tools/push-config.sh).
 */
public class SettingsActivity extends Activity {

    private EditText urlField;
    private EditText intervalField;

    @Override
    protected void onResume() {
        super.onResume();
        PowerCycle.settingsOpen = true;
        PowerCycle.restoreTimeout(this);
        PowerCycle.wifi(this, true);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    @Override
    protected void onPause() {
        PowerCycle.settingsOpen = false;
        super.onPause();
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.settings);

        urlField = (EditText) findViewById(R.id.settings_url);
        intervalField = (EditText) findViewById(R.id.settings_interval);

        urlField.setText(Config.url(this));
        intervalField.setText(String.valueOf(Config.intervalSeconds(this)));

        ((Button) findViewById(R.id.settings_save)).setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                save();
            }
        });
    }

    private void save() {
        int interval = Config.DEFAULT_INTERVAL_SECONDS;
        try {
            interval = Integer.parseInt(intervalField.getText().toString().trim());
        } catch (NumberFormatException e) {
            Toast.makeText(this, "Interval must be a whole number of seconds",
                    Toast.LENGTH_LONG).show();
            return;
        }
        Config.save(this, urlField.getText().toString(), interval);
        Toast.makeText(this, "Saved", Toast.LENGTH_SHORT).show();
        finish();
    }
}
