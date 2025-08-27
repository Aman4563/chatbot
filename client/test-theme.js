// Test script to verify theme functionality
console.log('Testing theme functionality...');

// Test localStorage
const testLocalStorage = () => {
  try {
    const saved = localStorage.getItem('chatbot-settings');
    console.log('LocalStorage settings:', saved);
    if (saved) {
      const parsed = JSON.parse(saved);
      console.log('Parsed settings:', parsed);
      console.log('Current theme:', parsed.websiteTheme);
    }
  } catch (error) {
    console.error('LocalStorage test failed:', error);
  }
};

// Test DOM classes
const testDOMClasses = () => {
  const root = document.documentElement;
  console.log('HTML classes:', root.className);
  console.log('Data theme attribute:', root.getAttribute('data-theme'));
  console.log('Has dark class:', root.classList.contains('dark'));
  console.log('Has light class:', root.classList.contains('light'));
};

// Test system preference
const testSystemPreference = () => {
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  console.log('System prefers dark mode:', isDark);
};

// Run tests
testLocalStorage();
testDOMClasses();
testSystemPreference();

// Function to manually apply theme
window.applyTheme = (theme) => {
  const root = document.documentElement;
  
  // Remove existing classes
  root.classList.remove('light', 'dark');
  
  if (theme === 'dark') {
    root.classList.add('dark');
    console.log('Manually applied dark theme');
  } else if (theme === 'light') {
    root.classList.add('light');
    console.log('Manually applied light theme');
  }
  
  // Update data attribute
  root.setAttribute('data-theme', theme);
  
  console.log('Theme applied:', theme);
  testDOMClasses();
};

console.log('Theme test functions available:');
console.log('- applyTheme("dark") - Apply dark theme');
console.log('- applyTheme("light") - Apply light theme');
