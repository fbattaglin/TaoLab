/**
 * Lightweight wrapper over `streamlit-component-lib`'s lifecycle messages.
 *
 * Streamlit hosts each custom component in an iframe. The Python side
 * sends `RENDER_EVENT` messages with `args` and `theme`, and the component
 * is expected to (a) render with those args and (b) call `setFrameHeight`
 * after layout so the host iframe sizes correctly. We keep things minimal
 * and avoid the React HOC from the lib since our components are functional.
 */

type Theme = {
  base?: "light" | "dark";
  primaryColor?: string;
  backgroundColor?: string;
  secondaryBackgroundColor?: string;
  textColor?: string;
  font?: string;
};

export type RenderPayload<A> = {
  args: A;
  theme?: Theme;
  disabled?: boolean;
};

type Listener<A> = (payload: RenderPayload<A>) => void;

const RENDER_EVENT = "streamlit:render";
const COMPONENT_READY = "streamlit:componentReady";
const SET_FRAME_HEIGHT = "streamlit:setFrameHeight";
const SET_COMPONENT_VALUE = "streamlit:setComponentValue";

function postToStreamlit(type: string, data: Record<string, unknown> = {}) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...data }, "*");
}

export function onRender<A>(listener: Listener<A>) {
  window.addEventListener("message", (event: MessageEvent) => {
    if (event.data?.type !== RENDER_EVENT) return;
    listener({
      args: event.data.args as A,
      theme: event.data.theme as Theme,
      disabled: event.data.disabled as boolean,
    });
  });
  postToStreamlit(COMPONENT_READY, { apiVersion: 1 });
}

export function setFrameHeight(height?: number) {
  postToStreamlit(SET_FRAME_HEIGHT, height ? { height } : {});
}

export function setComponentValue(value: unknown) {
  postToStreamlit(SET_COMPONENT_VALUE, { value, dataType: "json" });
}
