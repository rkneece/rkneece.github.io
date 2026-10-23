// Gesture math tests complement the browser checks of native controls/history.
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync(__dirname + '/viewer.js', 'utf8');
const body = source.slice(source.indexOf('  class PanZoom {'), source.indexOf('  const mapSurface ='));
const PanZoom = new Function('ResizeObserver', body + ';return PanZoom;')(class {observe(){}});
function surface(swipe) {
  const style = {setProperty(){}};
  const viewport = {clientWidth:390,clientHeight:500,addEventListener(){},setPointerCapture(){},getBoundingClientRect(){return {left:0,top:0}}};
  const content = {style};
  return new PanZoom(viewport,content,{swipe});
}
const event=(id,x,y)=>({pointerId:id,clientX:x,clientY:y,target:{closest(){return null;}}});
const map=surface();map.load(1);const fit=map.snapshot();
assert.equal(map.s,1);map.zoom(2);assert.equal(map.s,2);
map.down(event(1,100,100));map.move(event(1,130,140));map.up(event(1,130,140));
assert.equal(map.s,2);assert(map.x>-159);
map.fit();assert.equal(map.s,1);assert.equal(map.x,(390-map.w)/2);
map.down(event(1,100,200));map.down(event(2,200,200));
map.move(event(2,300,200));assert.equal(map.s,2);
map.up(event(2,300,200));map.up(event(1,100,200));
const saved=map.snapshot();const restored=surface();restored.load(1,saved);
assert.equal(restored.s,saved.s);assert(Math.abs(restored.snapshot().cx-saved.cx)<1e-9);
let direction=0;const photo=surface(delta=>direction=delta);photo.load(16/9);
photo.down(event(1,250,180));photo.move(event(1,90,185));photo.up(event(1,90,185));assert.equal(direction,1);
direction=0;photo.zoom(2);photo.down(event(1,250,180));photo.move(event(1,90,185));photo.up(event(1,90,185));assert.equal(direction,0);
photo.fit();photo.down(event(1,200,200));photo.down(event(2,300,200));photo.move(event(2,360,200));photo.up(event(2,360,200));photo.up(event(1,200,200));assert.equal(direction,0);
map.zoom(100);assert.equal(map.s,6);map.zoom(.00001);assert.equal(map.s,1);
console.log('PASS: fit, zoom limits, drag, pinch, transform restoration, swipe, zoomed swipe suppression, pinch swipe suppression');
