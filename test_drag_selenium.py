import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json

def test_drag():
    print("Starting driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get("http://localhost:5000")
    print("Page loaded.")
    time.sleep(2)
    
    # Enable 3D mode
    driver.execute_script("document.getElementById('toggle3D').click();")
    time.sleep(1)
    
    # Enter focus mode on the first room
    driver.execute_script("""
        const room = document.querySelector('.blueprint-room');
        const ev = new MouseEvent('dblclick', {bubbles: true, cancelable: true, view: window});
        room.dispatchEvent(ev);
    """)
    time.sleep(1)
    
    # Get the first furniture
    furn = driver.execute_script("""
        const f = document.querySelector('.furniture-item');
        return {
            x: f.style.left, 
            y: f.style.top,
            id: f.getAttribute('data-furn-id')
        };
    """)
    print("Initial furniture:", furn)
    
    # Attempt to drag
    furn_elem = driver.find_element(By.CSS_SELECTOR, '.furniture-item')
    
    action = ActionChains(driver)
    action.click_and_hold(furn_elem).move_by_offset(50, 50).release().perform()
    time.sleep(1)
    
    # Check new position
    furn_new = driver.execute_script("""
        const f = document.querySelector('.furniture-item');
        return {
            x: f.style.left, 
            y: f.style.top
        };
    """)
    print("New furniture:", furn_new)
    
    driver.quit()

if __name__ == "__main__":
    test_drag()
