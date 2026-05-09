import{a as c,j as e,c as l,r,u as d,o}from"./Stepper-BtSQAc7q.js";/**
 * @license lucide-react v0.454.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x=c("CircleCheck",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["path",{d:"m9 12 2 2 4-4",key:"dzmm74"}]]);/**
 * @license lucide-react v0.454.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const g=c("CircleSlash",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["line",{x1:"9",x2:"15",y1:"15",y2:"9",key:"1dfufj"}]]);/**
 * @license lucide-react v0.454.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h=c("Pause",[["rect",{x:"14",y:"4",width:"4",height:"16",rx:"1",key:"zuxfzm"}],["rect",{x:"6",y:"4",width:"4",height:"16",rx:"1",key:"1okwgv"}]]),u={ship:{label:"Ship it.",Icon:x,wrap:"bg-success/5 ring-1 ring-success/30",halo:"bg-success/15 text-success",labelClass:"text-success"},hold:{label:"Hold.",Icon:h,wrap:"bg-warning/5 ring-1 ring-warning/30",halo:"bg-warning/15 text-warning",labelClass:"text-warning"},dont_ship:{label:"Don't ship.",Icon:g,wrap:"bg-danger/5 ring-1 ring-danger/30",halo:"bg-danger/15 text-danger",labelClass:"text-danger"}};function m({state:s,headline:n,subtitle:a}){const t=u[s],{Icon:i}=t;return e.jsxs("div",{className:`rounded-card ${t.wrap} p-6 font-sans flex items-start gap-5`,children:[e.jsx("div",{className:`flex-none flex h-14 w-14 items-center justify-center rounded-full ${t.halo}`,children:e.jsx(i,{size:28,strokeWidth:2.25})}),e.jsxs("div",{className:"min-w-0",children:[e.jsx("div",{className:`text-2xl font-semibold tracking-tightish ${t.labelClass}`,children:t.label}),e.jsx("div",{className:"mt-1.5 text-base leading-relaxed text-indigo-ink",children:n}),a&&e.jsx("div",{className:"mt-2 text-sm text-slate",children:a})]})]})}function p(){const[s,n]=r.useState(null),a=d([s]);return r.useEffect(()=>{o(t=>n(t.args))},[]),s?e.jsx("div",{ref:a,className:"px-1 py-2",children:e.jsx(m,{state:s.state,headline:s.headline,subtitle:s.subtitle})}):e.jsx("div",{ref:a})}l(document.getElementById("root")).render(e.jsx(r.StrictMode,{children:e.jsx(p,{})}));
