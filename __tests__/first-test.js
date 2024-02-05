const VariableSelector = require('../bin/js/v4-VariableSelector');

/* mccli's error function prints to log and exits the program.
It should perhaps be throwing an error in general,
but for now we just override it for this test.
*/
let error = require('../bin/js/error');
jest.mock('../bin/js/error');
error.mockImplementation((msg) => {throw new Error(msg);});

/* previous line had working directory same as this test file,
while the reference to monte.conf below seems to have the project
working directory. Maybe test() sets the context?
*/

function newVS() {
    let master = {};
    return new VariableSelector(master, './__tests__/monte.conf') ;
}

test("check basic run with paths", () => {

   let errRE = /monte.conf has section for \w+\.  Unknown; expected one/
   // must wrap error in additional function call
   expect(() => newVS()).toThrow(errRE);
})