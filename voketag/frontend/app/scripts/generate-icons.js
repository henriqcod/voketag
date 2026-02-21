const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const publicDir = path.join(__dirname, '../public');
const svgPath = path.join(publicDir, 'icon.svg');

async function generate() {
  const svg = fs.readFileSync(svgPath);
  for (const size of [192, 512]) {
    const outPath = path.join(publicDir, `icon-${size}.png`);
    await sharp(svg)
      .resize(size, size)
      .png()
      .toFile(outPath);
    console.log(`Generated ${outPath}`);
  }
}

generate().catch(console.error);
