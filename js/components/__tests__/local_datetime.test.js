import { shallowMount } from '@vue/test-utils'

import LocalDatetime from '../local_datetime'

describe('LocalDatetime', () => {
  const wrapper = shallowMount(LocalDatetime, {
    propsData: { timestamp: '1977-05-25 00:00:00' },
  })

  it('renders a time element', () => {
    expect(wrapper.html()).toContain('<time')
    expect(wrapper.html()).toContain('May 25 1977')
  })

  it('matches snapshot', () => {
    expect(wrapper).toMatchSnapshot()
  })

  it('allows specifying a custom format', () => {
    const wrapperWithCustomFormat = shallowMount(LocalDatetime, {
      propsData: {
        timestamp: '1977-05-25 00:00:00',
        format: 'MMM do yy',
      },
    })
    expect(wrapperWithCustomFormat).toMatchSnapshot()
  })
})
