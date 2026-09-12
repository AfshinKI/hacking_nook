package com.hackingnook.panel;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;

/** Small monochrome overlay, drawn locally without modifying the downloaded image. */
public class BatteryView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private int percent = -1;
    private boolean charging;

    public BatteryView(Context context, AttributeSet attrs) {
        super(context, attrs);
    }

    public void setBattery(int value, boolean isCharging) {
        if (percent == value && charging == isCharging) {
            return;
        }
        percent = value;
        charging = isCharging;
        setContentDescription("Battery " + (percent < 0 ? "unknown" : percent + "%")
                + (charging ? ", charging" : ""));
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        canvas.save();
        canvas.scale(getWidth() / 88f, getHeight() / 28f);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(Color.WHITE);
        canvas.drawRect(0, 0, 88, 28, paint);
        paint.setColor(Color.BLACK);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(2);
        canvas.drawRect(5, 7, 29, 21, paint);
        paint.setStyle(Paint.Style.FILL);
        canvas.drawRect(30, 11, 33, 17, paint);
        if (percent > 0) {
            canvas.drawRect(8, 10, 8 + 18 * percent / 100f, 18, paint);
        }
        paint.setTextSize(14);
        canvas.drawText((percent < 0 ? "?" : percent + "%") + (charging ? "+" : ""),
                38, 19, paint);
        canvas.restore();
    }
}
