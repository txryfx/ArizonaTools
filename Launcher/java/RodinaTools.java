package com.arizona.launcher;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.ConnectivityManager;
import android.net.LinkProperties;
import android.net.Network;
import android.os.Build;
import android.provider.Settings;
import android.util.Log;
import android.widget.Toast;

public class RodinaTools {

    private static boolean isInitialized = false;
    private static Boolean showAdsThisLaunch;

    public static boolean isActiveAdBlocker(Activity activity, Context context) {
        ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            Network activeNetwork = cm.getActiveNetwork();
            if (activeNetwork != null) {
                LinkProperties linkProperties = cm.getLinkProperties(activeNetwork);
                if (linkProperties != null) {
                    String privateDnsHost = linkProperties.getPrivateDnsServerName();
                    if (privateDnsHost != null) {
                        String dns = privateDnsHost.toLowerCase();
                        String[] adBlockers = new String[] {
                            "adguard", "nextdns", "controld", "blokada", "rethinkdns",
                            "comss", "mullvad", "ahadns", "dnsforge", "dnswarden",
                            "dnsbunker", "blahdns", "dns0.eu", "dns4eu", "adaway",
                            "hagezi", "oisd", "pi-hole", "pihole", "adblock",
                            "adfree", "anti-ad", "blocker"
                        };
                        for (String blocker : adBlockers) {
                            if (dns.contains(blocker)) {
                                Log.w("RodinaTools", "Detected AD blocker: " + privateDnsHost);
                                return true;
                            }
                        }
                    }
                }
            }
        }
        return false;
    }

    public static boolean isShowAd(Context context) {
        SharedPreferences sp = context.getSharedPreferences("Rodina", Context.MODE_PRIVATE);
        if (!sp.getBoolean("check", false)) {
            sp.edit().putBoolean("check", true).apply();
            return false;
        }
        return true;
    }

    public static synchronized void initialize(Activity activity) {

        if (isInitialized) { return; }
        isInitialized = true;
        Context context = activity;

        new Thread(() -> {
            try {
                if (!com.arizona.launcher.CheckUpdate.isNeedUpdate(activity, context)) {
                    com.arizona.launcher.AssetExtractor.unpackAssets(activity, context);
                }
            } catch (Exception e) {
                Log.e("RodinaTools", "Error update/assets: ", e);
            }
        }).start();
    }

    public static void onLauncherResumed(Activity activity) {
        try {
            if (showAdsThisLaunch == null) {
                showAdsThisLaunch = false;
                if (!isShowAd(activity)) {
                    Log.i("RodinaTools", "Unity Ads skipped on the first launcher start");
                    return;
                }
                if (isActiveAdBlocker(activity, activity)) {
                    showPrivateDnsDialog(activity);
                    return;
                }
                showAdsThisLaunch = true;
            }
            if (showAdsThisLaunch) {
                Ads.onLauncherResumed(activity);
            }
        } catch (RuntimeException | LinkageError e) {
            Log.e("RodinaTools", "Unity Ads startup failed", e);
        }
    }

    private static void showPrivateDnsDialog(Activity activity) {
        new AlertDialog.Builder(activity)
                .setTitle("ℹ️ Обнаружен AD Blocker (Private DNS) ℹ️")
                .setMessage("Данный Lua лаунчер распространяется бесплатно, а реклама при запуске "
                        + "(в игре её нету) помогает поддерживать лаунчер 💖\n\n"
                        + "Вы используете Private DNS, который может блокировать показ рекламы.\n\n"
                        + "Для продолжения отключите частный DNS в настройках.")
                .setPositiveButton("Открыть настройки", (dialog, which) -> {
                    try {
                        activity.startActivity(new Intent("android.settings.PRIVATE_DNS_SETTINGS"));
                    } catch (Exception e) {
                        try {
                            activity.startActivity(new Intent(Settings.ACTION_WIRELESS_SETTINGS));
                        } catch (Exception ex) {
                            Toast.makeText(activity, "Настройки → Сеть → DNS", Toast.LENGTH_LONG).show();
                        }
                    }
                    activity.finishAffinity();
                })
                .setNegativeButton("Закрыть", (dialog, which) -> activity.finishAffinity())
                .setCancelable(false)
                .show();
    }
}
