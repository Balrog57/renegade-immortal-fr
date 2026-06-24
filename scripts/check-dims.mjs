import sharp from 'sharp';
const files = [
  'Book 1.webp','Book 2.webp','Book 3.webp','Book 4.webp','Book 5.webp',
  'Book 6.webp','Book 7.webp','Book 8.webp','Book 9.webp','Book 10.webp',
  'Book 11.webp','Book 12.png','Book 13.png'
];
for (const f of files) {
  try {
    const meta = await sharp('public/wiki/images/'+f).metadata();
    const r = (meta.width/meta.height).toFixed(3);
    console.log(f+': '+meta.width+'x'+meta.height+' ratio='+r);
  } catch(e) { console.log(f+': ERROR '+e.message); }
}
