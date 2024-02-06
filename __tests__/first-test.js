const VariableSelector = require('../bin/js/v4-VariableSelector');

/* mccli's error function prints to log and exits the program.
It should perhaps be throwing an error in general,
but for now we just override it for this test.
*/
let error = require('../bin/js/v4-logging');
jest.mock('../bin/js/v4-logging', ()=>{
    const originalModule = jest.requireActual('../bin/js/v4-logging');
    return {
        ...originalModule,
        error: jest.fn((msg) => {throw new Error(msg);})
    }
});


/* previous line had working directory same as this test file,
while the reference to monte.conf below seems to have the project
working directory. Maybe test() sets the context?
*/

function newVS(master, fname) {
    return new VariableSelector(master, fname) ;
}

test("check basic run with paths", () => {

   let errRE = /monte.conf has section for \w+\.  Unknown; expected one/
   // must wrap error in additional function call
   expect(() => newVS({}, './__tests__/monte.conf')).toThrow(errRE);
})

test("basic scan of monte.conf", ()=>{
    let master = {};
    let vs = newVS(master, './__tests__/monte2.conf');
    //toHaveLength doesn't work on Maps
    expect(master.sources.size).toBe(2);
    // check key converted to lower case
    expect(master.sources.has("TARGETS_OUTPUT")).toBeFalsy();
    expect(master.sources.has("targets_output")).toBeTruthy();
    let sds = master.sources.get("targets_output");
    //check case is preserved where appropriate
    expect(sds.basename).toBe("targets_output");
    expect(sds.ifname).toBe("TARGETS_OUTPUT.CSV");
    /* currently no public interface to check for a match,
    and the variable the patterns are held in is private.
    */
})