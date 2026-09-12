const fs=require('fs'), path=require('path');
const here=__dirname;
let s=fs.readFileSync(path.join(here,'workflow_capture.cjs'),'utf8');
s=s.replace(/function progress\(status, details\) \{[\s\S]*?\n\}/,'function progress() {}');
s=s.replace(/      const fp=path.join\(here,'progress.json'\);[\s\S]*?\n    \}/,'    }');
fs.writeFileSync(path.join(here,'sky_capture.cjs'),s);
const poses={photo09:JSON.parse(fs.readFileSync(path.join(here,'elevation_poses.json'),'utf8')).photo09,photo11:JSON.parse(fs.readFileSync(path.join(here,'lake_r2_poses.json'),'utf8')).photo11};
fs.writeFileSync(path.join(here,'sky_poses.json'),JSON.stringify(poses,null,2));
