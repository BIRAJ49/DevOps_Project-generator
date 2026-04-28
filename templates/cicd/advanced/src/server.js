import express from 'express'

const app = express()
const port = process.env.PORT || 8080

app.get('/health', (_request, response) => {
  response.json({ status: 'healthy' })
})

app.listen(port, () => {
  console.log(`release-gateway listening on ${port}`)
})

