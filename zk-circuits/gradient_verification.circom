pragma circom 2.0.0;

include "circomlib/poseidon.circom";

template GradientVerification() {
    // Public inputs
    signal input modelHash;
    signal input gradientHash;
    
    // Private inputs
    signal input model[100];  // Simplified: assume model has 100 parameters
    signal input gradient[100];
    
    // Compute hashes
    component modelHasher = Poseidon(100);
    component gradientHasher = Poseidon(100);
    
    for (var i = 0; i < 100; i++) {
        modelHasher.inputs[i] <== model[i];
        gradientHasher.inputs[i] <== gradient[i];
    }
    
    // Verify hashes match public inputs
    modelHash === modelHasher.out;
    gradientHash === gradientHasher.out;
}

component main = GradientVerification();
