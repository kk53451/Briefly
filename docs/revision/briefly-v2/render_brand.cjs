const path = require('path');
const sharp = require(process.env.BRIEFLY_SHARP_PATH || 'sharp');
const root = path.join(__dirname, 'assets');
(async () => {
  for (const name of ['logo', 'logo-black', 'logo-white']) {
    await sharp(path.join(root, `${name}.svg`), { density: 350 }).resize({ width: 1600 }).png().toFile(path.join(root, `${name}-1600.png`));
  }
  for (const size of [48, 64, 128, 180, 192, 512, 1024]) {
    await sharp(path.join(root, 'app-icon.svg'), { density: 800 }).resize(size, size).png().toFile(path.join(root, `app-icon-${size}.png`));
  }
  for (const size of [180, 192, 512, 1024]) {
    await sharp(path.join(root, 'app-icon-square.svg'), { density: 800 }).resize(size, size).png().toFile(path.join(root, `app-icon-square-${size}.png`));
  }
  console.log('Rendered approved wordmarks and full-name app icons.');
})().catch(error => { console.error(error); process.exit(1); });
