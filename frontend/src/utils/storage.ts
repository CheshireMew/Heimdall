export const getLocalStorage = (): Storage | null => {
  if (typeof window === 'undefined') return null
  try {
    // Some browser modes expose window but throw while reading localStorage.
    return window.localStorage
  } catch {
    return null
  }
}
