package com.hackingnook.panel;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.provider.Settings;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/** Atomic last-good-image and screensaver files: failed writes retain the old frame. */
final class FrameStore {
    private static final File DIRECTORY = new File("/media/screensavers/NookPanel");

    static Bitmap load(Context context) {
        BitmapFactory.Options options = new BitmapFactory.Options();
        options.inPreferredConfig = Bitmap.Config.RGB_565;
        return BitmapFactory.decodeFile(new File(context.getFilesDir(), "last-good.png").getPath(), options);
    }

    static void save(Context context, Bitmap bitmap) throws IOException {
        write(bitmap, new File(context.getFilesDir(), "last-good.png"));
    }

    static void screensaver(Context context, Bitmap bitmap) throws IOException {
        if (!DIRECTORY.isDirectory() && !DIRECTORY.mkdirs()) throw new IOException("Screensaver storage unavailable");
        File frame = new File(DIRECTORY, "panel.png");
        write(bitmap, frame);
        if (!Config.prefs(context).contains("previous_screensaver_dir")) {
            Config.prefs(context).edit()
                    .putString("previous_screensaver_dir", Settings.System.getString(context.getContentResolver(), "screensaver_dir"))
                    .putString("previous_screensaver_file", Settings.System.getString(context.getContentResolver(), "screensaver_current_file"))
                    .putString("previous_screensaver_banner", Settings.System.getString(context.getContentResolver(), "mod.option.hide_screensaver_banner"))
                    .commit();
        }
        if (!Settings.System.putString(context.getContentResolver(), "screensaver_dir", DIRECTORY.getPath())
                || !Settings.System.putString(context.getContentResolver(), "screensaver_current_file", frame.getName())) {
            throw new IOException("Could not select dashboard screensaver");
        }
        Settings.System.putInt(context.getContentResolver(), "mod.option.hide_screensaver_banner", 1);
    }

    private static void write(Bitmap bitmap, File target) throws IOException {
        // Keep the incomplete file outside the selected screensaver directory.
        File temporary = File.createTempFile("nookpanel-", ".tmp", target.getParentFile().getParentFile());
        try {
            FileOutputStream stream = new FileOutputStream(temporary);
            try {
                if (!bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)) throw new IOException("PNG encoding failed");
                stream.flush();
                stream.getFD().sync();
            } finally {
                stream.close();
            }
            if (!temporary.renameTo(target)) throw new IOException("Could not replace " + target);
        } finally {
            if (temporary.exists()) temporary.delete();
        }
    }
}
