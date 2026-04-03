const fs = require('fs');
const glob = new Bun.Glob('src/**/*.tsx');

for await (const file of glob.scan('.')) {
  let content = fs.readFileSync(file, 'utf8');
  let newContent = content;

  // Replace <Grid item xs={12} sm={6} md={4}> -> <Grid size={{xs: 12, sm: 6, md: 4}}>
  const regex = /<Grid\s+item\s+xs={(\d+)}(?:\s+sm={(\d+)})?(?:\s+md={(\d+)})?/g;
  newContent = newContent.replace(regex, (match, xs, sm, md) => {
    let sizeParts = [`xs: ${xs}`];
    if (sm) sizeParts.push(`sm: ${sm}`);
    if (md) sizeParts.push(`md: ${md}`);
    return `<Grid size={{ ${sizeParts.join(', ')} }}`;
  });

  // What about naked <Grid item> without sizes? like in login/register pages
  newContent = newContent.replace(/<Grid\s+item\s*>/g, `<Grid>`);

  if (content !== newContent) {
    fs.writeFileSync(file, newContent);
    console.log('Fixed', file);
  }
}
