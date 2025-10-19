class Clock:
    """
    Relógio lógico simples utilizado para manter a ordem de eventos no sistema distribuído.
    """

    count: int

    def __init__(self):
        """
        Inicializa o relógio com valor zero.
        """
        self.count = 0

    def increment(self):
        """
        Incrementa o valor do relógio em 1 e imprime o novo valor.
        Este método deve ser chamado a cada evento local ou mensagem recebida.
        """
        self.count += 1
        print(f"=> Atualizando relogio para {self.count}")

    def update(self, new_clock: int) -> bool:
        """
        Atualiza o valor do clock para o valor informado por parâmetro.
        O valor só será atualizado caso seja maior que o valor do clock atual.
        """
        if new_clock > self.count:
            self.count = int(new_clock)
            return True
        return False
