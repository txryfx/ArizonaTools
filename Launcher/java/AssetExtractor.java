package com.arizona.launcher;

import android.content.Context;

import android.content.res.AssetManager;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.os.Environment;
import android.util.Log;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;

import android.app.Activity;

import android.app.AlertDialog;

public class AssetExtractor {

    public static void unpackAssets(Activity activity, Context context) {
        SharedPreferences sp = context.getSharedPreferences("Rodina", Context.MODE_PRIVATE);
        String unpackedVersion = sp.getString("neomloader_version", "");
        String currentVersion = getLauncherVersion(context);
        
        if (unpackedVersion.equals(currentVersion)) {
            Log.i("RodinaTools", "NeoMLoader already unpacked for this version, skipping");
            return;
        }

        String folderName = "neomloader";
        File[] mediaDirs = context.getExternalMediaDirs();
        File outputFolder = new File(mediaDirs.length > 0 ? mediaDirs[0] : null, folderName);

        if (outputFolder == null || (!outputFolder.exists() && !outputFolder.mkdirs())) {
            showErrorDialog(activity, context, "❗ NeoMLoader Error ❗", "Не удалось автоматически создать папку /neomloader\n\nПопробуйте перезапустить лаунчер или создайте её вручную.");
            return;
        }

        try {
            AssetManager assetManager = context.getAssets();
            String[] files = assetManager.list(folderName);
            if (files == null || files.length == 0) {
                showErrorDialog(activity, context, "❗ NeoMLoader Error ❗", "У вас битый APK без нужных файлов!\n\n" + "Обратитесь к разработчику: vk.ru/sayxxion");
                return;
            }

            for (String fileName : files) {
                File outFile = new File(outputFolder, fileName);
                if (isDirectory(assetManager, folderName + "/" + fileName)) {
                    outFile.mkdirs();
                    unpackAssetsRecursive(assetManager, folderName + "/" + fileName, outFile);
                } else {
                    copyFile(assetManager, folderName + "/" + fileName, outFile);
                }
            }
            
            sp.edit().putString("neomloader_version", currentVersion).apply();
            Log.i("RodinaTools", "NeoMLoader unpacked for version " + currentVersion);

        } catch (IOException e) {
            Log.e("RodinaTools", "Error extractor: " + e);
            File fixFile = new File(outputFolder, "lib/imgui_piemenu.lua");
            if (!fixFile.exists()) {
                showErrorDialog(activity, context, "❗NeoMLoader Error❗", "Не удалось автоматически установить нужные библиотеки для работоспособности!\n\nПопробуйте перезапустить лаунчер или установите их вручную.");
            }
        }
    }

    private static boolean isDirectory(AssetManager assetManager, String path) {
        try {
            String[] list = assetManager.list(path);
            return list != null && list.length > 0;
        } catch (IOException e) {
            return false;
        }
    }

    private static void unpackAssetsRecursive(AssetManager assetManager, String path, File destination) throws IOException {
        String[] files = assetManager.list(path);
        if (files == null || files.length == 0) return;

        for (String fileName : files) {
            File outFile = new File(destination, fileName);
            String newPath = path + "/" + fileName;
            if (isDirectory(assetManager, newPath)) {
                outFile.mkdirs();
                unpackAssetsRecursive(assetManager, newPath, outFile);
            } else {
                copyFile(assetManager, newPath, outFile);
            }
        }
    }

    private static void copyFile(AssetManager assetManager, String assetPath, File outFile) throws IOException {
        if (outFile.exists()) { outFile.delete(); }

        File parent = outFile.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();
        }

        InputStream in = assetManager.open(assetPath);
        FileOutputStream out = new FileOutputStream(outFile);

        byte[] buffer = new byte[1024];
        int read;
        while ((read = in.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }

        in.close();
        out.flush();
        out.close();
    }

    private static void showErrorDialog(Activity activity, Context context, String title, String message) {
        activity.runOnUiThread(() -> {
            AlertDialog.Builder alertDialog = new AlertDialog.Builder(context)
                    .setTitle(title)
                    .setMessage(message)
                    .setPositiveButton("Ок", (dialogInterface, i) -> activity.finishAffinity())
                    .setCancelable(false);

            AlertDialog dialog = alertDialog.create();
            dialog.setCanceledOnTouchOutside(false);
            dialog.show();
        });
    }

    private static String getLauncherVersion(Context context) {
        try {
            return context.getPackageManager()
                    .getPackageInfo(context.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "";
        }
    }

}
