using System;
using HarmonyLib;
using UnityEngine;

namespace com.github.lhervier.ksp.fix.constructiontoolbar
{
    /// <summary>
    /// Installs the fixes the settings turn on, once, when KSP starts: from then on, the closed warp-to-morning
    /// drawer below the time display no longer takes the pointer over the EVA construction tools, and the
    /// construction mode's block moves down below the time display when the next alarm shows.
    /// </summary>
    [KSPAddon(KSPAddon.Startup.Instantly, true)]
    public class KSPFixConstructionToolbar : MonoBehaviour
    {
        private const string HarmonyId = "com.github.lhervier.ksp.fix.constructiontoolbar";

        private void Start()
        {
            Settings.Load();
            Log.Info($"Version {typeof(KSPFixConstructionToolbar).Assembly.GetName().Version}, " +
                $"closedDrawerLetsPointerThrough {Settings.ClosedDrawerLetsPointerThrough}, " +
                $"constructionModeBelowAlarm {Settings.ConstructionModeBelowAlarm}, log level {Log.Level}");
            Harmony harmony = new Harmony(HarmonyId);
            if (Settings.ClosedDrawerLetsPointerThrough)
            {
                try
                {
                    ClosedDrawerFilter.Install(harmony);
                    Log.Info("Closed drawer fix installed");
                }
                catch (Exception e)
                {
                    Log.Error($"Could not install the closed drawer fix, the drawer takes the pointer as on stock: {e}");
                }
            }
            if (Settings.ConstructionModeBelowAlarm)
            {
                try
                {
                    ConstructionBelowAlarm.Install(harmony);
                    Log.Info("Construction mode below alarm fix installed");
                }
                catch (Exception e)
                {
                    Log.Error("Could not install the construction mode below alarm fix, the time display covers the " +
                        $"construction mode's block as on stock when the next alarm shows: {e}");
                }
            }
        }
    }
}
