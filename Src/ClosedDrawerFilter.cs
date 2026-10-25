using HarmonyLib;
using KSP.UI;
using UnityEngine;

namespace com.github.lhervier.ksp.fix.constructiontoolbar
{
    /// <summary>
    /// Keeps the mask of the warp-to-morning drawer, below the time display, from taking the pointer while the
    /// drawer is closed. On stock, that mask is an invisible rectangle under the time display that always takes
    /// the pointer: resting it there, over the top of the EVA construction tools, slides the drawer down, and
    /// its sunrise button lands under the pointer, so the click meant for the Place tool warps to the next
    /// morning. Open or sliding, the drawer takes the pointer as on stock: the mask then bridges the time
    /// display and the sunrise button, and keeps the drawer open on the way.
    /// </summary>
    internal class ClosedDrawerFilter : MonoBehaviour, ICanvasRaycastFilter
    {
        private UITimeWarpHoverController hover;

        /// <summary>Patches the time display's hover controller so that each one gets the filter.</summary>
        public static void Install(Harmony harmony)
        {
            harmony.Patch(AccessTools.Method(typeof(UIHoverSlidePanel), "Start"),
                postfix: new HarmonyMethod(typeof(ClosedDrawerFilter), nameof(StartPostfix)));
        }

        private static void StartPostfix(UIHoverSlidePanel __instance)
        {
            // Other hover panels (the abort button's...) share the base class: only the time display's has the drawer.
            UITimeWarpHoverController hover = __instance as UITimeWarpHoverController;
            if (hover == null)
            {
                return;
            }
            if (hover.fixedMask == null || hover.panel == null)
            {
                Log.Warning($"No drawer mask on the time display {hover.name}: the drawer takes the pointer as on stock");
                return;
            }
            if (hover.fixedMask.GetComponent<ClosedDrawerFilter>() != null)
            {
                return;
            }
            hover.fixedMask.gameObject.AddComponent<ClosedDrawerFilter>().hover = hover;
            Log.Debug($"Filter put on the drawer mask {hover.fixedMask.name} of {hover.name}");
        }

        /// <summary>
        /// Returns whether the mask, and the drawer it clips, may take the pointer: only while the drawer is not
        /// closed, that is not resting at its normal position.
        /// </summary>
        public bool IsRaycastLocationValid(Vector2 screenPoint, Camera eventCamera)
        {
            // Unity asks a filter even when disabled; a disabled one lets the drawer be, as Mask does.
            if (!isActiveAndEnabled || hover == null || hover.panel == null)
            {
                return true;
            }
            // MoveToState ends a slide by setting the position exactly, so a closed drawer is at its normal position.
            return (hover.panel.anchoredPosition - hover.positionNormal).sqrMagnitude > 0.0001f;
        }
    }
}
