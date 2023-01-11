import {html, LitElement} from './lit-all.min.js';

export class CharacterImage extends LitElement {
    render() {
        return html`
            <h1>Hello World</h1>
        `
    }

    createRenderRoot() {
        return this;
    }
}

window.customElements.define('character-image', CharacterImage)