'use strict';
const nReadLines = require("n-readlines");
const { error } = require('./v4-logging');
const SimDataSource = require('./v4-SimDataSource');

const sectionRE = /\[\s*((?<full>(?<base>\S.*)(?<ext>\.csv))|(?<simple>\S.*)(?<=\S))\s*\]/i;
const sectionNames = new Set(["targets_output", "totresults", "calib"]);
const sepRE = /\s*,\s*|\s+/;

module.exports = class VariableSelector {
   constructor(master, configfile) {
      let i, line, match, csvname, base, ext, v, rawv, sds;
      const reader = new nReadLines(configfile);
      let sections = new Map(); // key is lowercase base name, value is a SimDataSource
      master.sources = sections;
      while (line=reader.next()) {
         line = line.toString('ascii');
         // strip out comment
         i = line.indexOf("#")
         if (i==0)
            // pure comment
            continue;
         if (i>0)
            line = line.slice(0, i);
   
         if (match = line.match(sectionRE)){
            // process section heading
            // ((?<full>(?<base>\S.*)(?<ext>\.csv))|(?<simple>\S.*)
            csvname = match.groups.full;
            if (csvname) {
               base = match.groups.base;
               ext = match.groups.ext;
            } else {
               base = match.groups.simple;
               if (! base)
                  error("monte.conf has an empty section heading.");
               ext = ".csv";
               csvname = base + ext;
            }
            // at this point base, ext and csvname are all set up.
            if (!sectionNames.has(base.toLowerCase()))
               error(`monte.conf has section for ${base}.  Unknown; expected one of ${[...sectionNames].join(", ")}.`);
            sds = new SimDataSource(base, csvname);
            sections.set(base.toLowerCase(), sds);
            continue;
         } else {
            if (!sds)
               // still in preamble
               continue;
         };
         // handle list of variables
         for (rawv of line.split(sepRE)){
            // blanks keep slipping through
            if (!rawv)
               continue;
            v = rawv;
            // convert pseudo-shell globs to RE
            if (v.startsWith("*"))
                  v = "."+v;
            if (v.endsWith("*"))
                  v = v.slice(0, v.length-1)+".*";
            /* Most v will likely not be regular expressions.
            But any effort to figure out what is and isn't an RE
            will burden either the programmer or the user.
            So we store them both ways.
            */
            sds.addPattern(rawv, new RegExp("^"+v+"$", "i"));
         }
      };
   };
}
