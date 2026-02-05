describe('Randomness Uncontrolled Smell', () => {
  
  it('should complete full upload workflow and display metrics', () => {
  
    cy.visit('http://localhost:3000/')
    
   
    cy.visit('http://localhost:3000/upload-python')
    
  
    cy.contains('Static Tool').click()
   
    cy.get('input[type="file"]').selectFile('X:\\UNI\\MAGISTRALE\\ISTA\\CODESMILE\\smell_ai\\test\\system_testing\\e2e_testingCypress\\CR3.py')
    
    
    cy.contains('CR3.py').should('be.visible')
     
    cy.contains('Upload Code (Static Mode)').click()
    
    
    cy.wait(2000)
    

  })
  
})