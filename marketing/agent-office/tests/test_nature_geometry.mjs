import test from 'node:test';
import assert from 'node:assert/strict';
import { createPalmCrownGeometry, createTropicalLeafGeometry, createBeachGeometry, coastRadius } from '../office/static/office-nature.js';

function validMesh(geometry) {
  for (const attribute of Object.values(geometry.attributes)) assert.ok(attribute.array.every(Number.isFinite), 'finite attributes are required by the GPU');
  assert.ok(geometry.index.array.every(index => index < geometry.attributes.position.count));
  assert.equal(geometry.index.count % 3, 0);
  geometry.computeBoundingBox();
}

test('palm crown has separate tapered leaflets, stable vein normals and bounded wind weights', () => {
  const crown = createPalmCrownGeometry(); validMesh(crown);
  const { min, max } = crown.boundingBox;
  assert.ok(max.x - min.x > 6 && max.z - min.z > 6, 'crown spreads out from the trunk');
  assert.ok(min.y > -2 && max.y < 3, 'fronds arch and droop around their attachment');
  const wind = crown.attributes.windWeight.array;
  assert.ok(wind.some(w => w === 0) && wind.some(w => w > .9));
  assert.ok(wind.every(w => w >= 0 && w <= 1.2));
  crown.dispose();
});

test('tropical leaves fit their pots and keep their roots still in the wind', () => {
  const shrub = createTropicalLeafGeometry(); validMesh(shrub);
  assert.ok(shrub.boundingBox.min.y >= 0 && shrub.boundingBox.max.y < 2);
  assert.ok(shrub.boundingBox.max.x - shrub.boundingBox.min.x < 4);
  const positions = shrub.attributes.position, wind = shrub.attributes.windWeight;
  for (let i = 0; i < positions.count; i++) if (positions.getY(i) < .13) assert.equal(wind.getX(i), 0);
  shrub.dispose();
});

test('beach faces upward and slopes below the water along the same irregular coast', () => {
  const beach = createBeachGeometry(); validMesh(beach);
  assert.ok(beach.boundingBox.min.y < -1.6 && beach.boundingBox.max.y <= -.5);
  const normals = beach.attributes.normal;
  assert.ok(Array.from({length: normals.count}, (_, i) => normals.getY(i)).filter(y => y > 0).length > normals.count * .8);
  const positions = beach.attributes.position;
  for (let i = positions.count - 129; i < positions.count; i++) {
    const x = positions.getX(i) / 26, z = (positions.getZ(i) - 2) / 23;
    assert.ok(Math.abs(Math.hypot(x, z) / coastRadius(Math.atan2(x, z)) - 1.18) < .00001);
  }
  beach.dispose();
});
