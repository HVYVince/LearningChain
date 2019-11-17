from BlockchainController import BlockchainController
from DaemonController import DaemonController

blockchain_controller = BlockchainController()
daemon_controller = DaemonController(blockchain_controller)

while True:
    blockchain_controller.update()
    daemon_controller.update()
