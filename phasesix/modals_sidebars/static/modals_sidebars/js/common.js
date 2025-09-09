/* eventString: comma separated string of event names to dispatch */
export function dispatch(eventString) {
    if (eventString) {
        for (let e of eventString.split(",")) {
            document.dispatchEvent(
                new CustomEvent(e, {
                    detail: null,
                    bubbles: true,
                }),
            );
        }
    }
}
