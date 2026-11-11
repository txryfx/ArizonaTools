package com.arizona.launcher;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import android.widget.Toast;
import android.app.AlertDialog;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class CheckUpdate {

    public static boolean isNeedUpdate(Activity activity, Context context) {
        try {
            URL url = new URL("https://raw.githubusercontent.com/txryfx/ArizonaTools/refs/heads/main/Launcher/launcher.json");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(3000);
            conn.setReadTimeout(3000);

            StringBuilder response = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
            }
            conn.disconnect();

            String appVersion = context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName;
            String packageName = context.getPackageName();

            int resId = context.getResources().getIdentifier("custom_version", "string", context.getPackageName());
            String customVersion = resId != 0 ? context.getString(resId) : appVersion;

            JSONObject jsonObject = new JSONObject(response.toString());
            String updateUrl = jsonObject.getString("url");
            
            String currentVersion = jsonObject.getString(packageName.contains("rodina") ? "rodina_version" : "version");
            
            String remoteCustomVersion = jsonObject.optString("custom_version", currentVersion);
            
            boolean forceUpdate = jsonObject.optBoolean("force_update", false);

            if (!appVersion.equals(currentVersion) || !customVersion.equals(remoteCustomVersion)) {
                
                activity.runOnUiThread(() -> {
                    AlertDialog.Builder builder = new AlertDialog.Builder(context)
                            .setTitle("ℹ️ NeoMLoader Update ℹ️")
                            .setMessage("Установленный у вас лаунчер версии " + customVersion + " не актуален!\n\n"
                                      + "Используйте версию " + remoteCustomVersion + " для стабильной игры.")
                            .setPositiveButton("Скачать", (dialogInterface, i) -> {
                                Intent browserIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(updateUrl));
                                context.startActivity(browserIntent);
                                activity.finishAffinity();
                            })
                            .setCancelable(!forceUpdate);

                    if (!forceUpdate) {
                        builder.setNegativeButton("Игнор", (dialogInterface, i) -> {
                            new Thread(() -> com.arizona.launcher.AssetExtractor.unpackAssets(activity, context)).start();
                            dialogInterface.dismiss();
                        });
                    }
                    
                    builder.show();
                });
                return true;
            }

        } catch (Exception e) {
            Log.e("RodinaTools", "Error update: ", e);
        }

        return false;
    }
}