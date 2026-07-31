// UI-level types: themes, locales, formatting helpers.

export type ThemeId = 'dark' | 'gray' | 'light'
export type LocaleId = 'en' | 'fr'

export interface ThemeOption {
  id: ThemeId
  label: string
}

export interface LocaleOption {
  id: LocaleId
  label: string
  name: string
}

/** Colour/label descriptor returned by the score helpers. */
export interface ScoreColor {
  text: string
  bg: string
}

export interface ScoreStatus {
  ring: string
  text: string
  bg: string
  bar: string
  labelKey: string
}

/** Translation interpolation parameters. */
export type I18nParams = Record<string, string | number>

/** Structured content consumed by the InfoTip component (from the i18n catalog). */
export interface InfoTipLevel {
  range: string
  label: string
  tone: 'good' | 'neutral' | 'warn' | 'bad'
}

export interface InfoTipContent {
  title: string
  text?: string
  formula?: string
  levels?: InfoTipLevel[]
  tip?: string
}

/** Selectable data categories in the reset modal. */
export interface ResetOptions {
  caches: boolean
  backtests: boolean
  watchlist: boolean
  portfolio: boolean
  tickers: boolean
}
