const VariableSelector = require('../bin/js/v4-VariableSelector');

/* previous line had working directory same as this test file,
while the reference to monte.conf below seems to have the project
working directory. Maybe test() sets the context?
*/

function newVS() {
    let master = {};
    return new VariableSelector(master, './py_tests/monte.conf') ;
}

test("check basic run with paths", () => {

   let errRE = /monte.conf has section for \w+\.  Unknown; expected one/
   // must wrap error in additional function call
   expect(() => newVS()).toThrow(errRE);
})