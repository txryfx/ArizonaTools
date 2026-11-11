package com.arizona.launcher;

import android.app.Activity;
import android.app.Application;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.ViewTreeObserver;
import android.widget.Toast;

import com.unity3d.ads.IUnityAdsInitializationListener;
import com.unity3d.ads.IUnityAdsLoadListener;
import com.unity3d.ads.IUnityAdsShowListener;
import com.unity3d.ads.UnityAds;
import com.unity3d.ads.UnityAdsShowOptions;

public final class Ads {
    private static final String TAG = "RodinaTools";
    private static final long STARTUP_TIMEOUT_MS = 20_000L;
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private enum State { IDLE, INITIALIZING, LOADING, READY, DONE }

    private static State state = State.IDLE;
    private static Activity foreground;
    private static Application application;
    private static ViewTreeObserver focusObserver;
    private static final ViewTreeObserver.OnWindowFocusChangeListener FOCUS_LISTENER =
            hasFocus -> { if (hasFocus) showWhenReady(); };
    private static final Runnable STARTUP_TIMEOUT = () ->
            fail("startup", "timed out while " + state);

    static void onLauncherResumed(Activity activity) {
        if (state == State.DONE || activity.isFinishing() || activity.isDestroyed()) {
            return;
        }
        if (foreground != activity) {
            stopObservingWindow();
            foreground = activity;
            focusObserver = activity.getWindow().getDecorView().getViewTreeObserver();
            focusObserver.addOnWindowFocusChangeListener(FOCUS_LISTENER);
        }
        if (state == State.IDLE) {
            initialize(activity.getApplication());
        }
        showWhenReady();
    }

    public static void onLauncherPaused(Activity activity) {
        if (foreground == activity) {
            stopObservingWindow();
        }
    }

    private static void initialize(Application app) {
        application = app;
        state = State.INITIALIZING;
        MAIN.postDelayed(STARTUP_TIMEOUT, STARTUP_TIMEOUT_MS);
        try {
            if (AdsConfig.TEST_MODE) {
                UnityAds.setDebugMode(true);
            }
            Log.i(TAG, "Unity Ads init: sdk=" + UnityAds.getVersion()
                    + " package=" + app.getPackageName() + " gameId=" + AdsConfig.GAME_ID
                    + " placement=" + AdsConfig.PLACEMENT_ID + " testMode=" + AdsConfig.TEST_MODE);
            UnityAds.initialize(app, AdsConfig.GAME_ID, AdsConfig.TEST_MODE,
                    new IUnityAdsInitializationListener() {
                        @Override
                        public void onInitializationComplete() {
                            MAIN.post(Ads::load);
                        }

                        @Override
                        public void onInitializationFailed(UnityAds.UnityAdsInitializationError error,
                                                           String message) {
                            MAIN.post(() -> {
                                if (state == State.INITIALIZING) {
                                    fail("init", error + " " + message);
                                }
                            });
                        }
                    });
        } catch (RuntimeException | LinkageError e) {
            fail("init", e);
        }
    }

    private static void load() {
        if (state != State.INITIALIZING) {
            return;
        }
        state = State.LOADING;
        Log.i(TAG, "Unity Ads load: " + AdsConfig.PLACEMENT_ID);
        try {
            UnityAds.load(AdsConfig.PLACEMENT_ID, new IUnityAdsLoadListener() {
                @Override
                public void onUnityAdsAdLoaded(String placementId) {
                    MAIN.post(() -> {
                        if (state == State.LOADING) {
                            Log.i(TAG, "Unity Ads loaded: " + placementId);
                            state = State.READY;
                            showWhenReady();
                        }
                    });
                }

                @Override
                public void onUnityAdsFailedToLoad(String placementId, UnityAds.UnityAdsLoadError error,
                                                    String message) {
                    MAIN.post(() -> {
                        if (state == State.LOADING) {
                            fail("load", placementId + " " + error + " " + message);
                        }
                    });
                }
            });
        } catch (RuntimeException | LinkageError e) {
            fail("load", e);
        }
    }

    private static void showWhenReady() {
        Activity activity = foreground;
        if (state != State.READY || activity == null || activity.isFinishing()
                || activity.isDestroyed() || !activity.hasWindowFocus()) {
            return;
        }
        finishRequest();
        Log.i(TAG, "Unity Ads show: " + AdsConfig.PLACEMENT_ID);
        try {
            UnityAds.show(activity, AdsConfig.PLACEMENT_ID, new UnityAdsShowOptions(),
                    new IUnityAdsShowListener() {
                        @Override
                        public void onUnityAdsShowStart(String placementId) {
                            Log.i(TAG, "Unity Ads started: " + placementId);
                            toast("[RodinaTools]\nℹ️ Реклама помогает поддерживать лаунчер", Toast.LENGTH_LONG);
                        }

                        @Override
                        public void onUnityAdsShowClick(String placementId) { }

                        @Override
                        public void onUnityAdsShowComplete(String placementId,
                                                           UnityAds.UnityAdsShowCompletionState result) {
                            Log.i(TAG, "Unity Ads completed: " + placementId + " " + result);
                            if (result == UnityAds.UnityAdsShowCompletionState.COMPLETED) {
                                toast("[RodinaTools]\n❤️ Спасибо ❤️", Toast.LENGTH_SHORT);
                            } else {
                                toast("[RodinaTools]\nРеклама пропущена", Toast.LENGTH_SHORT);
                            }
                        }

                        @Override
                        public void onUnityAdsShowFailure(String placementId, UnityAds.UnityAdsShowError error,
                                                          String message) {
                            Log.e(TAG, "Unity Ads show failed: " + placementId + " " + error + " " + message);
                        }
                    });
        } catch (RuntimeException | LinkageError e) {
            Log.e(TAG, "Unity Ads show failed", e);
        }
    }

    private static void toast(String text, int duration) {
        MAIN.post(() -> Toast.makeText(application, text, duration).show());
    }

    private static void fail(String stage, String message) {
        Log.w(TAG, "Unity Ads " + stage + " failed: " + message);
        finishRequest();
    }

    private static void fail(String stage, Throwable error) {
        Log.e(TAG, "Unity Ads " + stage + " failed", error);
        finishRequest();
    }

    private static void finishRequest() {
        state = State.DONE;
        MAIN.removeCallbacks(STARTUP_TIMEOUT);
        stopObservingWindow();
    }

    private static void stopObservingWindow() {
        if (focusObserver != null) {
            // The view can merge its original observer into a new one when attached.
            if (!focusObserver.isAlive()) {
                focusObserver = foreground.getWindow().getDecorView().getViewTreeObserver();
            }
            if (focusObserver.isAlive()) {
                focusObserver.removeOnWindowFocusChangeListener(FOCUS_LISTENER);
            }
            focusObserver = null;
        }
        foreground = null;
    }
}
