const CATEGORY_PREFIX_STORAGE_KEY = 'vocabularyCategoryPrefix';
const COLUMN_SEPARATOR_STORAGE_KEY = 'vocabularyColumnSeparator';
const PARSED_VOCABULARY_STORAGE_KEY = 'parsedVocabulary';

function vocabularyApp() {
  return {
    query: '',
    randomCount: 10,
    fileName: '',
    fileText: '',
    categoryPrefix: '#',
    columnSeparator: '    ',
    loading: false,
    error: '',
    settingsOpen: false,
    allCategories: [],
    allEntries: [],
    entries: [],

    init() {
      this.categoryPrefix = localStorage.getItem(CATEGORY_PREFIX_STORAGE_KEY) || this.categoryPrefix;
      this.columnSeparator = localStorage.getItem(COLUMN_SEPARATOR_STORAGE_KEY) || this.columnSeparator;
      this.restoreParsedVocabulary();
    },

    get filteredEntries() {
      const needle = this.query.toLowerCase();

      if (!needle) {
        return this.entries;
      }

      return this.entries.filter((entry) => {
        return entry.source.toLowerCase().includes(needle)
          || entry.translation.toLowerCase().includes(needle)
          || entry.example.toLowerCase().includes(needle)
          || entry.category.toLowerCase().includes(needle);
      });
    },

    get groupedEntries() {
      return this.allCategories
        .map((category) => ({
          id: category.id,
          name: category.name,
          entries: this.filteredEntries.filter((entry) => entry.category === category.name),
        }))
        .filter((category) => category.entries.length);
    },

    get sourceLabel() {
      return this.fileName ? `Reading vocabulary from ${this.fileName}.` : 'Choose a .txt file to get started.';
    },

    loadSelectedFile(event) {
      const [file] = event.target.files;

      if (!file) {
        return;
      }

      if (!file.name.toLowerCase().endsWith('.txt')) {
        this.clearVocabulary();
        this.error = 'Choose a .txt file.';
        return;
      }

      this.fileName = file.name;
      this.error = '';

      const reader = new FileReader();

      reader.onload = () => {
        this.fileText = reader.result || '';
        this.parseCurrentFile();
      };

      reader.onerror = () => {
        this.clearVocabulary();
        this.error = 'The selected file could not be read.';
      };

      reader.readAsText(file);
    },

    parseCurrentFile() {
      if (!this.fileText) {
        this.clearVocabulary();
        return;
      }

      const { categories, skipped } = this.parseVocabulary(this.fileText);

      this.allCategories = categories;
      this.allEntries = categories.flatMap((category) => category.entries);
      this.entries = this.allEntries;
      this.query = '';

      if (!this.allEntries.length) {
        this.error = 'No valid vocabulary rows were found. Check the category prefix and column separator.';
      } else if (skipped) {
        this.error = `${skipped} ${skipped === 1 ? 'row was' : 'rows were'} skipped because a required column was missing.`;
        this.storeParsedVocabulary();
      } else {
        this.error = '';
        this.storeParsedVocabulary();
      }
    },

    saveSettings() {
      this.categoryPrefix = this.categoryPrefix || '#';
      this.columnSeparator = this.columnSeparator || '    ';
      localStorage.setItem(CATEGORY_PREFIX_STORAGE_KEY, this.categoryPrefix);
      localStorage.setItem(COLUMN_SEPARATOR_STORAGE_KEY, this.columnSeparator);
      this.parseCurrentFile();
    },

    clearVocabulary() {
      this.allCategories = [];
      this.allEntries = [];
      this.entries = [];
    },

    restoreParsedVocabulary() {
      const savedVocabulary = localStorage.getItem(PARSED_VOCABULARY_STORAGE_KEY);

      if (!savedVocabulary) {
        return;
      }

      try {
        const parsed = JSON.parse(savedVocabulary);

        this.fileName = parsed.fileName || '';
        this.allCategories = parsed.categories || [];
        this.allEntries = this.allCategories.flatMap((category) => category.entries || []);
        this.entries = this.allEntries;
      } catch (error) {
        localStorage.removeItem(PARSED_VOCABULARY_STORAGE_KEY);
      }
    },

    storeParsedVocabulary() {
      localStorage.setItem(PARSED_VOCABULARY_STORAGE_KEY, JSON.stringify({
        fileName: this.fileName,
        categories: this.allCategories,
      }));
    },

    parseVocabulary(text) {
      const categories = [];
      let currentCategory = this.createCategory('Uncategorized');
      let skipped = 0;
      const separatorPattern = this.getSeparatorPattern();

      text.split(/\r?\n/).forEach((line) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return;
        }

        if (trimmed.startsWith(this.categoryPrefix)) {
          const categoryName = trimmed.slice(this.categoryPrefix.length).trim();

          if (categoryName) {
            currentCategory = this.createCategory(categoryName);
            categories.push(currentCategory);
          }

          return;
        }

        const columns = trimmed.split(separatorPattern).map((column) => column.trim());

        if (!columns[0] || !columns[1]) {
          skipped += 1;
          return;
        }

        if (!categories.includes(currentCategory)) {
          categories.push(currentCategory);
        }

        currentCategory.entries.push({
          id: this.generateId(),
          category: currentCategory.name,
          source: columns[0],
          translation: columns[1],
          example: columns.slice(2).join(this.columnSeparator),
        });
      });

      return {
        categories: categories.filter((category) => category.entries.length),
        skipped,
      };
    },

    getSeparatorPattern() {
      if (this.columnSeparator === '\\t') {
        return /\t+/;
      }

      if (this.columnSeparator === '\\s{4,}') {
        return /\s{4,}/;
      }

      return new RegExp(this.escapeRegExp(this.columnSeparator) + '+');
    },

    escapeRegExp(value) {
      return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    chooseRandomEntries() {
      const count = Number.parseInt(this.randomCount, 10);

      if (!Number.isFinite(count) || count < 1) {
        this.error = 'Enter a number greater than 0.';
        return;
      }

      this.error = '';
      this.query = '';
      this.entries = this.shuffleEntries(this.allEntries).slice(0, Math.min(count, this.allEntries.length));
    },

    shuffleEntries(entries) {
      const shuffled = [...entries];

      for (let index = shuffled.length - 1; index > 0; index -= 1) {
        const randomIndex = Math.floor(Math.random() * (index + 1));
        [shuffled[index], shuffled[randomIndex]] = [shuffled[randomIndex], shuffled[index]];
      }

      return shuffled;
    },

    createCategory(name) {
      return {
        id: this.generateId(),
        name,
        entries: [],
      };
    },

    generateId() {
      if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
      }

      return `${Date.now().toString(36)}-${Math.floor(Math.random() * 0xFFFFFFFF).toString(36)}`;
    },
  };
}
