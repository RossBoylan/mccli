module.exports = class CSVConfig {
   year = 0;
   age = 2;
   sex = 3;
   dataPath = path.join(".", "outputs")
   constructor(ifname) {
      this.ifname = ifname;
      this.ifpath = path.join(this.dataPath, ifname);
      this.#patterns = new Map();
   }
   <<CSVConfig pattern handling>>
   <<CSVConfig codebook handling>>
   <<CSVConfig csv input handling>>
}
