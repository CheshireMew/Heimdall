import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

const attachInterceptors = (client: AxiosInstance) => {
    client.interceptors.request.use(
        (config: InternalAxiosRequestConfig) => {
            return config
        },
        (error: unknown) => {
            return Promise.reject(error)
        }
    )

    client.interceptors.response.use(
        (response: AxiosResponse) => {
            return response
        },
        (error: unknown) => {
            console.error('API Request Failed:', error)
            return Promise.reject(error)
        }
    )

    return client
}

const createClient = (timeout: number): AxiosInstance => attachInterceptors(
    axios.create({
        baseURL: '/api/v1',
        timeout,
        headers: {
            'Content-Type': 'application/json'
        }
    })
)

const service: AxiosInstance = createClient(15000)
export const longTaskRequest: AxiosInstance = createClient(0)

export default service
