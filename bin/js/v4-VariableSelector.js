const sectionRE = /\[\s*((?<full>(?<base>\S.*)(?<ext>\.csv))|(?<simple>\S.*)(?<=\S))\s*\]/i;
const sectionNames = Set(["targets_output", "totresults", "calib"])
const sepRE = /(\s*,\s*)|(\s+)/;
module.exports = class VariableSelector {
   constructor(master, configfile) {
      let i, line, match, csvname, base, ext, current, v, rawv;
      const reader = new nReadLines(configfile);
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
               base = match.group.base;
               ext = match.group.ext;
            } else {
               base = match.group.simple;
               if (! base)
                  // Trying to use error() defined in runSims.js
                  error("monte.conf has an empty section heading.");
               ext = ".csv";
               csvname = base + ext;
            }
            // at this poin base, ext and csvname are all set up.
            if (!sectionNames.has(base.toLowerCase()))
               error("monte.conf has section for ${base}.  Unknown; expected one of ${sectionNames}.");
            current = {
                  /* varPatterns has keys that are the raw text entered
                  and values that are regular expressions.
                  If the raw text is matched, the item will be removed.
                  */
                  varPatterns: new Map(),
            }
            master.csvs.set(csvname, current);
            continue;
         };
         // handle list of variables
         for (rawv of line.split(sepRE)){
            v = rawv
            // convert pseudo-shell globs to RE
            if (v.startsWith("*"))
                  v = "."+v
            if (v.endsWith("*"))
                  v = v.slice(0, v.length-1)+".*"
            /* Most v will likely not be regular expressions.
            But any effort to figure out what is and isn't an RE
            will burden either the programmer or the user.
            So we store them both ways.
            */
            current.varPatterns.set(rawv, new RegExp("^"+v+"$", "i"));
         }
      };
   };
}
