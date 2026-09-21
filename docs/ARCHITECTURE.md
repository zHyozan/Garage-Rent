# Arquitetura — Garage Rent

## Domínios principais

### Space
Representa uma garagem, vaga ou galpão. O anúncio pertence a um usuário e possui preço, período de cobrança, localização pública aproximada, endereço exato privado, dimensões e comodidades.

### Favorite
Relacionamento único entre usuário e anúncio.

### Reservation
Representa a intenção/contrato de locação entre locatário e espaço. Estados: pendente, confirmada, recusada, cancelada e concluída.

## Regras de segurança do MVP
- Somente usuários autenticados criam anúncios.
- Somente o proprietário altera/exclui seu anúncio.
- O proprietário não pode reservar o próprio espaço.
- Reservas pendentes/confirmadas não podem se sobrepor.
- O endereço exato não é serializado publicamente.
- O endereço exato é liberado para proprietário ou locatário com reserva confirmada.
- Preço unitário e total da reserva ficam registrados como snapshot para evitar alteração retroativa do preço do anúncio.

## Evolução recomendada
Ao adicionar pagamentos e alto volume, migrar para PostgreSQL, usar transações com bloqueio adequado para disponibilidade, armazenar imagens fora do servidor web e introduzir trilhas de auditoria para mudanças sensíveis.
