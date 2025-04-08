const { execSync } = require('child_process');

// Set Node.js memory limit
process.env.NODE_OPTIONS = '--max_old_space_size=4096';

// Compile each module separately to avoid memory issues
const modules = ['interfaces', 'tokens', 'core', 'governance'];

console.log('Starting modular compilation...');

modules.forEach(module => {
  console.log(`\nCompiling ${module} module...`);
  try {
    execSync(`truffle compile --contracts_directory ./contracts/${module}`, { stdio: 'inherit' });
    console.log(`✅ ${module} module compiled successfully`);
  } catch (error) {
    console.error(`❌ Error compiling ${module} module`);
    process.exit(1);
  }
});

console.log('\nAll modules compiled successfully! 🎉');
