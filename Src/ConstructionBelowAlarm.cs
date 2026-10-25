using System;
using System.Reflection;
using HarmonyLib;
using KSP.UI;
using UnityEngine;

namespace com.github.lhervier.ksp.fix.constructiontoolbar
{
    /// <summary>
    /// Keeps the EVA construction mode's block, its tools and its list of parts, below the time display when the
    /// next alarm shows above it. On stock, the alarm clock button, left of the time display, shows the next alarm
    /// in a row above it and slides the time display down; the construction mode's block does not move, and the
    /// time display then covers the top of its tools and the first row of its list. Its top is moved down by as
    /// much as the time display, its bottom left where it is.
    /// </summary>
    internal class ConstructionBelowAlarm : MonoBehaviour
    {
        // FlightUIModeController.NextAlarmToggle sets the time display's In position to one of these.
        private static readonly FieldInfo WithoutNextAlarm = AccessTools.Field(typeof(FlightUIModeController), "withoutNextAlarm");
        private static readonly FieldInfo WithNextAlarm = AccessTools.Field(typeof(FlightUIModeController), "withNextAlarm");
        private static readonly FieldInfo BlockTransition =
            AccessTools.Field(typeof(EVAConstructionModeController), "constructionModeTransition");

        private UIPanelTransition transition;
        private RectTransform block;

        /// <summary>How far down the block is moved now, in the units of its parent.</summary>
        private float applied;

        /// <summary>Patches the construction mode's controller so that its block gets this component.</summary>
        public static void Install(Harmony harmony)
        {
            if (WithoutNextAlarm == null || WithNextAlarm == null || BlockTransition == null)
            {
                throw new MissingFieldException("FlightUIModeController.withoutNextAlarm, .withNextAlarm or " +
                    "EVAConstructionModeController.constructionModeTransition");
            }
            harmony.Patch(AccessTools.Method(typeof(EVAConstructionModeController), "Start"),
                postfix: new HarmonyMethod(typeof(ConstructionBelowAlarm), nameof(StartPostfix)));
        }

        private static void StartPostfix(EVAConstructionModeController __instance)
        {
            UIPanelTransition transition = BlockTransition.GetValue(__instance) as UIPanelTransition;
            if (transition == null || transition.states == null)
            {
                Log.Warning("No transition on the construction mode's block: it stays where it is when the next alarm shows");
                return;
            }
            if (transition.GetComponent<ConstructionBelowAlarm>() != null)
            {
                return;
            }
            ConstructionBelowAlarm component = transition.gameObject.AddComponent<ConstructionBelowAlarm>();
            component.transition = transition;
            component.block = (RectTransform)transition.transform;
            Log.Debug($"Construction mode's block {transition.name} follows the time display");
        }

        private void LateUpdate()
        {
            FlightUIModeController ui = FlightUIModeController.Instance;
            if (ui == null || ui.timeFrame == null)
            {
                return;
            }
            float target = ui.NextAlarmShowing ? Shift(ui) : 0f;
            if (Mathf.Approximately(target, applied))
            {
                return;
            }
            MoveDown(target - applied);
            Log.Debug(ui.NextAlarmShowing
                ? $"Next alarm shown: construction mode's block moved down by {target}"
                : "Next alarm hidden: construction mode's block back in its place");
            applied = target;
        }

        /// <summary>How far the time display goes down when the next alarm shows, in the units of the block's parent.</summary>
        private float Shift(FlightUIModeController ui)
        {
            float shift = (float)WithoutNextAlarm.GetValue(ui) - (float)WithNextAlarm.GetValue(ui);
            // The time display's position counts in the units of its own parent.
            return shift * ui.timeFrame.transform.parent.lossyScale.y / block.parent.lossyScale.y;
        }

        /// <summary>Moves the block's top down by delta, its bottom staying where it is, in every state of its transition.</summary>
        private void MoveDown(float delta)
        {
            // The transition sets the block's position from its states, In and Out: both go down, so that it does
            // not slide up or down as it comes in or goes out. The block stretches over its parent's height, its pivot
            // at its top: a smaller height keeps its bottom in place.
            foreach (UIPanelTransition.PanelPosition state in transition.states)
            {
                state.position.y -= delta;
            }
            block.anchoredPosition -= new Vector2(0f, delta);
            block.sizeDelta -= new Vector2(0f, delta);
        }
    }
}
