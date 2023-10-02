# Example 1 - CNF Usage Flow

```mermaid
graph TD;
    CNF<-->Application
    Application-->Database
    Application-->WebService
    WebService<-->CNF
    WebService<-->Database

    Database <--> CNF

```
