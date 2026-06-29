const VOCABULARY_ENDPOINT = 'https://vocabulary-teacher.onrender.com/vocabulary'
const VOCABULARY_CACHE_STORAGE_KEY = 'vocabularyCache'
const LANGUAGE_CACHE_STORAGE_KEY = 'targetLanguage'
const ALL_CATEGORIES = '__all__'

function vocabularyApp() {
  return {
    query: '',
    randomCount: 10,
    selectedCategory: ALL_CATEGORIES,
    loading: false,
    error: '',
    settingsOpen: false,
    hasActiveShuffle: false,
    allCategories: [],
    allEntries: [],
    entries: [],
    allLanguages: [
      { code: 'en', name: 'English' },
      { code: 'ar', name: 'العربية' },
    ],
    targetLanguage: 'en',
    displayMode: 'visible',

    init() {
      this.loadLanguage()
      this.loadDisplayMode()
      this.loadVocabulary()
    },

    get categoryEntries() {
      if (this.selectedCategory === ALL_CATEGORIES) {
        return this.allEntries
      }

      return this.allEntries.filter((entry) => entry.category === this.selectedCategory)
    },

    get filteredEntries() {
      const needle = this.normalizeText(this.query)

      if (!needle) {
        return this.entries
      }

      return this.entries.filter((entry) => {
        return this.normalizeText(entry[sourceLanguage]).includes(needle)
      })
    },

    get availableEntryCount() {
      return this.categoryEntries.length
    },

    setLanguage(language) {
      this.targetLanguage = language
      localStorage.setItem(LANGUAGE_CACHE_STORAGE_KEY, language)
      const cachedVocabulary = this.getCachedVocabulary()
      if (cachedVocabulary) {
        this.applyVocabulary(cachedVocabulary.data)
      }
    },

    loadLanguage() {
      this.targetLanguage = localStorage.getItem(LANGUAGE_CACHE_STORAGE_KEY) || 'en'
    },

    loadDisplayMode() {
      const saved = localStorage.getItem('displayMode')
      if (saved === 'flip' || saved === 'visible') {
        this.displayMode = saved
      }
    },

    setDisplayMode(mode) {
      this.displayMode = mode
      localStorage.setItem('displayMode', mode)
    },

    async loadVocabulary({ forceFetch = false } = {}) {
      this.error = ''
      this.loading = true

      // Show cached data immediately if available, even if expired.
      const cachedVocabulary = this.getCachedVocabulary({ allowExpired: true })
      if (cachedVocabulary) {
        this.applyVocabulary(cachedVocabulary.data)
        // If the cache is still fresh and we're not forcing, skip the fetch.
        if (!forceFetch && !this.isCacheExpired(cachedVocabulary)) {
          this.loading = false
          return
        }
      }

      try {
        const response = await fetch(VOCABULARY_ENDPOINT)

        if (!response.ok) {
          throw new Error(`Server antwortet mit ${response.status}`)
        }

        const vocabulary = await response.json()
        this.applyVocabulary(vocabulary)
        if (this.hasVocabularyContent(vocabulary)) {
          this.cacheVocabulary(vocabulary)
        } else {
          localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
        }
      } catch (error) {
        // Keep the stale cache — don't clear it. Just show an error.
        // If there was no cached data at all, show empty state.
        if (!cachedVocabulary) {
          this.clearVocabulary()
        }
        this.error = `Vokabeln konnten nicht geladen werden. ${error.message}`
      } finally {
        this.loading = false
      }
    },

    refreshVocabulary() {
      return this.loadVocabulary({ forceFetch: true })
    },

    isCacheExpired(cache) {
      if (!cache) return true
      const expiresAt = Number(cache.expiresAt)
      return !Number.isFinite(expiresAt) || Date.now() >= expiresAt
    },

    getCachedVocabulary({ allowExpired = false } = {}) {
      const rawCache = localStorage.getItem(VOCABULARY_CACHE_STORAGE_KEY)
      if (!rawCache) return null

      try {
        const cache = JSON.parse(rawCache)
        if (!cache.data) {
          localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
          return null
        }
        // If expired and we're not allowing expired, purge and return null.
        if (!allowExpired && this.isCacheExpired(cache)) {
          localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
          return null
        }
        return cache
      } catch (error) {
        localStorage.removeItem(VOCABULARY_CACHE_STORAGE_KEY)
        return null
      }
    },

    cacheVocabulary(vocabulary) {
      const expiresAt = this.getNextMidnightTimestamp()

      localStorage.setItem(
        VOCABULARY_CACHE_STORAGE_KEY,
        JSON.stringify({
          data: vocabulary,
          expiresAt,
        })
      )
    },

    hasVocabularyContent(vocabulary) {
      return Object.values(vocabulary || {}).some((entries) => {
        return Array.isArray(entries) && entries.length > 0
      })
    },

    getNextMidnightTimestamp() {
      const nextMidnight = new Date()
      nextMidnight.setHours(24, 0, 0, 0)
      return nextMidnight.getTime()
    },

    applyVocabulary(vocabulary) {
      const categories = Object.entries(vocabulary || {}).map(([name, entries], categoryIndex) => {
        return {
          id: this.createCategoryId(categoryIndex),
          name,
          entries: (Array.isArray(entries) ? entries : []).map((entry, index) => {
            const source = entry.source || entry.de || ''
            const translation = entry.translation || entry[this.targetLanguage] || entry.en || ''
            const sourceExample = entry.sourceExample || entry['example-de'] || ''
            const translationExample =
              entry.translationExample || entry[`example-${this.targetLanguage}`] || entry['example-en'] || ''
            return {
              id: this.createEntryId(categoryIndex, index),
              category: name,
              source,
              sourceExample,
              translation,
              translationExample,
            }
          }),
        }
      })

      this.allCategories = categories.filter((category) => category.entries.length)
      this.allEntries = this.allCategories.flatMap((category) => category.entries)
      this.selectedCategory = ALL_CATEGORIES
      this.entries = this.categoryEntries
      this.hasActiveShuffle = false
      this.query = ''
    },

    clearVocabulary() {
      this.allCategories = []
      this.allEntries = []
      this.entries = []
      this.selectedCategory = ALL_CATEGORIES
      this.hasActiveShuffle = false
    },

    selectCategory() {
      this.error = ''
      this.query = ''
      this.entries = this.categoryEntries
      this.hasActiveShuffle = false
    },

    chooseRandomEntries() {
      const count = Number.parseInt(this.randomCount, 10)

      if (!Number.isFinite(count) || count < 1) {
        this.error = 'Gib eine Zahl größer als 0 ein.'
        return
      }

      this.error = ''
      this.query = ''
      const availableEntries = this.categoryEntries
      this.entries = this.shuffleEntries(availableEntries).slice(0, Math.min(count, availableEntries.length))
      this.hasActiveShuffle = true
      this.settingsOpen = false
    },

    resetEntries() {
      this.error = ''
      this.query = ''
      this.entries = this.categoryEntries
      this.hasActiveShuffle = false
    },

    shuffleEntries(entries) {
      const shuffled = [...entries]

      for (let index = shuffled.length - 1; index > 0; index -= 1) {
        const randomIndex = Math.floor(Math.random() * (index + 1))
        const temp = shuffled[index]
        shuffled[index] = shuffled[randomIndex]
        shuffled[randomIndex] = temp
      }

      return shuffled
    },

    normalizeText(value) {
      return String(value || '').toLowerCase()
    },

    createCategoryId(index) {
      return `category-${index}`
    },

    createEntryId(categoryIndex, entryIndex) {
      return `entry-${categoryIndex}-${entryIndex}`
    },
  }
}
