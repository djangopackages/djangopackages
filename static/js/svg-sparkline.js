/*
svg-sparkline.js 1.0.10

MIT License

Copyright (c) 2024 Chris Burnell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

class SVGSparkline extends HTMLElement {
  static register(tagName) {
    if ("customElements" in window) {
      customElements.define(tagName || "svg-sparkline", SVGSparkline)
    }
  }

  static css = `
    :host {
      display: grid;
      display: inline-grid;
      grid-template-columns: 1fr 1fr;
      grid-template-rows: 1fr auto;
    }
    svg {
      inline-size: auto;
      grid-column: 1 / 3;
      grid-row: 1 / 2;
      padding: var(--svg-sparkline-padding, 0.375rem);
      overflow: visible;
    }
    :host(:not([curve])) svg:has(title),
    :host(:not([curve="true"])) svg:has(title) {
      overflow-y: hidden;
    }
    svg[aria-hidden] {
      pointer-events: none;
    }
    span {
      padding-inline: var(--svg-sparkline-padding, 0.375rem);
    }
    span:nth-of-type(1) {
      grid-column: 1 / 2;
      text-align: start;
    }
    span:nth-of-type(2) {
        grid-column: 2 / 3;
        text-align: end;
    }
    @media (prefers-reduced-motion: no-preference) {
      :host([animate]) {
        --duration: var(--svg-sparkline-animation-duration, var(--animation-duration, 1s));
        --first-delay: var(--svg-sparkline-animation-first-delay, var(--svg-sparkline-animation-delay, var(--animation-delay, 1s)));
        --second-delay: var(--svg-sparkline-animation-second-delay, calc(var(--duration) + var(--first-delay)));
      }
      :host([animate]) svg:first-of-type {
        clip-path: polygon(0 0, 0 0, 0 100%, 0 100%);
      }
      :host([visible]) svg:first-of-type {
        animation: swipe var(--duration) linear var(--first-delay) forwards;
      }
      :host([animate]) svg:last-of-type,
      :host([animate]) span {
        opacity: 0;
      }
      :host([visible]) svg:last-of-type,
      :host([visible]) span {
        animation: fadein var(--duration) linear var(--second-delay) forwards;
      }
    }
    @keyframes swipe {
      to {
        clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
      }
    }
    @keyframes fadein {
      to {
        opacity: 1;
      }
    }
  `

  static observedAttributes = ["values", "width", "height", "color", "curve", "endpoint", "endpoint-color", "endpoint-width", "fill", "gradient", "fill-color", "gradient-color", "line-width", "start-label", "end-label", "animation-duration", "animation-delay"]

  connectedCallback() {
    if (!this.getAttribute("values")) {
      console.error(`Missing \`values\` attribute!`, this)
      return
    }

    this.init()
  }

  render() {
    if (!this.hasAttribute("values")) {
      return
    }

    this.values = this.getAttribute("values").split(",")
    this.width = parseFloat(this.getAttribute("width")) || 200
    this.height = parseFloat(this.getAttribute("height")) || 36
    this.color = this.getAttribute("color")
    this.curve = this.hasAttribute("curve") && this.getAttribute("curve") !== "false"
    this.endpoint = this.getAttribute("endpoint") !== "false"
    this.endpointColor = this.getAttribute("endpoint-color")
    this.endpointWidth = parseFloat(this.getAttribute("endpoint-width")) || 6
    this.fill = this.hasAttribute("fill") && this.getAttribute("fill") !== "false"
    this.gradient = this.hasAttribute("gradient") && this.getAttribute("gradient") !== "false"
    this.gradientColor = this.getAttribute("fill-color") || this.getAttribute("gradient-color")
    this.lineWidth = parseFloat(this.getAttribute("line-width")) || 2
    this.startLabel = this.getAttribute("start-label")
    this.endLabel = this.getAttribute("end-label")

    const color = this.color || `var(--svg-sparkline-color, currentColor)`
    const endpointColor = this.endpointColor || `var(--svg-sparkline-endpoint-color, ${color})`
    const gradientColor = this.gradientColor || `var(--svg-sparkline-fill-color, var(--svg-sparkline-gradient-color, ${color}))`

    let content = []

    if (this.startLabel) {
      content.push(`<span>${this.startLabel}</span>`)
    }

    const title = this.title || `Sparkline ranging from ${this.getMinY(this.values)} to ${this.getMaxY(this.values)}.`;
    content.push(`
      <svg width="${this.width}px" height="${this.height}px" viewBox="${this.getViewBox(this.values)}" preserveAspectRatio="none" role="img">
        <title>${title}</title>
    `)

    let gradientID
    if (this.gradient) {
      gradientID = this.makeID(6)
      content.push(`
        <defs>
          <linearGradient id="svg-sparkline-gradient-${gradientID}" gradientTransform="rotate(90)">
            <stop offset="0%" stop-color="${gradientColor}" />
            <stop offset="100%" stop-color="transparent" />
          </linearGradient>
        </defs>
      `)
    }

    if (this.gradient || this.fill) {
      content.push(`
        <path
            d="${this.getPath(this.values, this.curve)} L ${this.getFinalX(this.values)} ${this.getAdjustedMaxY(this.values)} L 0 ${this.getAdjustedMaxY(this.values)} Z"
            fill="${this.fill ? gradientColor : `url('#svg-sparkline-gradient-${gradientID}')`}"
            stroke="transparent"
        />
      `)
    }

    content.push(`
      <path
          d="${this.getPath(this.values, this.curve)}"
          stroke="${color}"
          stroke-width="${this.lineWidth}"
          stroke-linecap="round"
          fill="transparent"
          vector-effect="non-scaling-stroke"
      />
    `)

    content.push(`</svg>`)

    if (this.endpoint) {
      content.push(`
        <svg width="${this.width}px" height="${this.height}px" viewBox="0 0 ${this.width} ${this.height}" preserveAspectRatio="xMaxYMid meet" aria-hidden="true">
          <circle r="${this.endpointWidth / 2}" cx="${this.width}" cy="${(this.height / this.getAdjustedMaxY(this.values)) * this.getFinalY(this.values)}" fill="${endpointColor}"></circle>
        </svg>
      `)
    }

    if (this.endLabel) {
      content.push(`<span>${this.endLabel}</span>`)
    }

    return content.join("")
  }

  getBaseCSS() {
    let sheet = new CSSStyleSheet()
    sheet.replaceSync(SVGSparkline.css)

    return sheet
  }

  setCSS() {
    let stylesheets = [this.getBaseCSS()]
    if (this.hasAttribute("animation-duration")) {
      let sheet = new CSSStyleSheet()
      sheet.replaceSync(`
        :host {
          --animation-duration: ${this.getAttribute("animation-duration")};
        }
      `)
      stylesheets.push(sheet)
    }
    if (this.hasAttribute("animation-delay")) {
      let sheet = new CSSStyleSheet()
      sheet.replaceSync(`
        :host {
          --animation-delay: ${this.getAttribute("animation-delay")};
        }
      `)
      stylesheets.push(sheet)
    }
    this.shadowRoot.adoptedStyleSheets = stylesheets
  }

  initTemplate() {
    if (this.shadowRoot) {
      if (this.innerHTML.trim() === "") {
        this.shadowRoot.innerHTML = this.render()
      } else {
        this.shadowRoot.innerHTML = this.innerHTML
        this.innerHTML = ""
      }
      return
    }

    this.attachShadow({ mode: "open" })

    this.setCSS()

    let template = document.createElement("template")
    template.innerHTML = this.render()
    this.shadowRoot.appendChild(template.content.cloneNode(true))

    const threshold = Math.min(Math.max(Number(this.getAttribute("threshold") || 0.333), 0), 1)

    if (this.hasAttribute("animate")) {
      const observer = new IntersectionObserver(
        (entries, observer) => {
          if (entries[0].intersectionRatio > threshold) {
            this.setAttribute("visible", true)
            observer.unobserve(this)
          }
        },
        { threshold: threshold }
      )
      observer.observe(this)
    }
  }

  init() {
    this.initTemplate()
  }

  attributeChangedCallback() {
    this.initTemplate()
    this.setCSS()
  }

  maxDecimals(value, decimals = 2) {
    return +value.toFixed(decimals)
  }

  getViewBox(values) {
    return `0 0 ${values.length - 1} ${this.getAdjustedMaxY(values)}`
  }

  lineCommand(point, i) {
    return `L ${i},${point}`
  }

  line(ax, ay, bx, by) {
    const lengthX = bx - ax
    const lengthY = by - ay

    return {
      length: Math.sqrt(Math.pow(lengthX, 2) + Math.pow(lengthY, 2)),
      angle: Math.atan2(lengthY, lengthX),
    }
  }

  controlPoint(cx, cy, px, py, nx, ny, reverse) {
    // When the current X,Y are the first or last point of the array,
    // previous or next X,Y don't exist. Replace with current X,Y.
    px = px || cx
    py = py || cy
    nx = nx || cx
    ny = ny || cy

    const line = this.line(px, py, nx, ny)

    const smoothing = 0.2
    const angle = line.angle + (reverse ? Math.PI : 0)
    const length = line.length * smoothing

    const x = cx + Math.cos(angle) * length
    const y = cy + Math.sin(angle) * length

    return [x, y]
  }

  bezierCommand(point, i, a, maxY) {
    const [csx, csy] = this.controlPoint(i - 1, a[i - 1], i - 2, a[i - 2], i, point)
    const [cex, cey] = this.controlPoint(i, point, i - 1, a[i - 1], i + 1, a[i + 1], true)

    return `C ${this.maxDecimals(csx)},${Math.min(maxY, this.maxDecimals(csy))} ${this.maxDecimals(cex)},${Math.min(maxY, this.maxDecimals(cey))} ${i},${point}`
  }

  getPath(values, curve) {
    return (
      values
        // flips each point in the vertical range
        .map((point) => Math.max(...values) - point + 1)
        // generate a string
        .reduce((acc, point, i, a) => {
          return i < 1 ? `M 0,${point}` : `${acc} ${curve ? this.bezierCommand(point, i, a, this.getAdjustedMaxY(values)) : this.lineCommand(point, i)}`
        }, "")
    )
  }

  getFinalX(values) {
    return values.length - 1
  }

  getFinalY(values) {
    return Math.max(...values) - values[values.length - 1] + 1
  }

  getMinY(values) {
    return Math.min(...values)
  }

  getMaxY(values) {
    return Math.max(...values)
  }

  getAdjustedMaxY(values) {
    return this.getMaxY(values) + 1
  }

  makeID(length) {
    const SEQUENCE = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return Array.from({ length: length }).reduce((id, _) => {
      return id + SEQUENCE.charAt(Math.floor(Math.random() * SEQUENCE.length))
    }, "")
  }
}

SVGSparkline.register()
